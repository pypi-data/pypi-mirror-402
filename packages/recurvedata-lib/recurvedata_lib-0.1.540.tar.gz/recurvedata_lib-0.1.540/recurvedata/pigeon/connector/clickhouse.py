import datetime
import functools
import json
import re
import shutil
import subprocess

import cytoolz as toolz
import requests
from infi.clickhouse_orm import fields
from sqlalchemy_clickhouse import connector as clickhouse

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.dbapi import ClosingCursor, DBAPIConnector, NullCursor, _ShowTableLikeMixin
from recurvedata.pigeon.schema import types
from recurvedata.pigeon.utils import fs


# Patch sqlalchemy_clickhouse, use requests session (keep alive)
def _send(self, data, settings=None, stream=False):
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not hasattr(self, "_session"):
        self._session = requests.session()
    params = self._build_params(settings)
    r = self._session.post(self.db_url, params=params, data=data, stream=stream)
    if r.status_code != 200:
        raise Exception(r.text)
    return r


clickhouse.Database._send = _send


class ParamEscaper(clickhouse.ParamEscaper):
    def escape_item(self, item):
        if item is None:
            return "NULL"
        elif isinstance(item, (int, float)):
            return self.escape_number(item)
        elif isinstance(item, str):
            return self.escape_string(item)
        elif isinstance(item, datetime.date):
            return self.escape_string(str(item))
        else:
            raise Exception("Unsupported object {}".format(item))


# Hack: sqlalchemy_clickhouse 的 ParamEscaper 不支持日期类型
clickhouse._escaper = ParamEscaper()

_clickhouse_type_to_canonical_type = {
    # pigeon 没有定义 uint, 用「更长」的 INT 表示，防止溢出
    "UInt8": types.INT16,
    "UInt16": types.INT32,
    "UInt32": types.INT64,
    "UInt64": types.INT64,
    "Int8": types.INT8,
    "Int16": types.INT16,
    "Int32": types.INT32,
    "Int64": types.INT64,
    "Float32": types.FLOAT32,
    "Float64": types.FLOAT64,
    "String": types.STRING,
    "FixedString": types.STRING,
    "Date": types.DATE,
    "DateTime": types.DATETIME,
    "Enum": types.STRING,
    "Array": types.JSON,
}

_canonical_type_to_clickhouse_type = {
    types.BOOLEAN: "UInt8",
    types.INT8: "Int8",
    types.INT16: "Int16",
    types.INT32: "Int32",
    types.INT64: "Int64",
    types.FLOAT32: "Float32",
    types.FLOAT64: "Float64",
    types.DATE: "Date",
    types.DATETIME: "DateTime",
    types.STRING: "String",
    types.JSON: "String",
}

_clickhouse_type_to_orm_filed = {
    "UInt8": fields.UInt8Field(),
    "UInt16": fields.UInt16Field(),
    "UInt32": fields.UInt32Field(),
    "UInt64": fields.UInt64Field(),
    "Int8": fields.Int8Field(),
    "Int16": fields.Int16Field(),
    "Int32": fields.Int32Field(),
    "Int64": fields.Int64Field(),
    "Float32": fields.Float32Field(),
    "Float64": fields.Float64Field(),
    "String": fields.StringField(),
    "Date": fields.DateField(),
}

nullable_type_p = re.compile(r"Nullable\((?P<inner_type_code>.*)\)")
array_type_p = re.compile(r"Array\((?P<inner_type_code>.*)\)")
low_cardinality_type_p = re.compile(r"LowCardinality\((?P<inner_type_code>.*)\)")


def _format_sql(operation, parameters=None):
    if parameters is None or not parameters:
        sql = operation
    else:
        sql = operation % clickhouse._escaper.escape_args(parameters)
    return sql


class WrappedCursor(ClosingCursor):
    @property
    def description(self):
        return self._description

    def execute(self, operation: str, parameters=None):
        is_response = self._determine_is_response(operation)
        self._cursor.execute(operation, parameters, is_response)

        # sqlalchemy-clickhouse 的 cursor 默认的查询方式，如果结果为空，则没有 description
        # 可以使用 FORMAT JSON 查询得到
        self._description = self._cursor.description
        if not self._cursor.description and is_response:
            self._description = self._get_cursor_description(operation, parameters)

    def _determine_is_response(self, query: str):
        # 简单判断是否 SELECT 查询
        keywords = ["INSERT", "CREATE", "ALTER", "DROP", "RENAME", "SET", "KILL QUERY", "ATTACH", "DETACH"]
        for kw in keywords:
            if re.search(f"\\b{kw}\\b", query, re.IGNORECASE):
                return False
        return True

    def _get_cursor_description(self, operation: str, parameters=None):
        query = _format_sql(operation, parameters)
        query += " FORMAT JSON"
        rv = self._cursor._db.raw(query)
        data = json.loads(rv)
        return [
            # name, type_code, display_size, internal_size, precision, scale, null_ok
            (x["name"], x["type"], None, None, None, None, True)
            for x in data["meta"]
        ]


class ClickHouseField(object):
    def __init__(self, name, type_code):
        self.name = name
        self.type_code = type_code  # ClickHouse 的类型，比如 Array(String)

        if self.is_array() or self.is_nullable() or self.is_low_cardinality():
            self.inner_type = self._infer_inner_type()
        else:
            self.inner_type = None

    def is_array(self):
        return self.type_code.startswith("Array")

    def is_nullable(self):
        return self.type_code.startswith("Nullable")

    def is_low_cardinality(self):
        return self.type_code.startswith("LowCardinality")

    def is_int(self):
        return self._real_type in ["UInt8", "UInt16", "UInt32", "UInt64", "Int8", "Int16", "Int32", "Int64"]

    def is_float(self):
        return self._real_type in ["Float32", "Float64"]

    def is_string(self):
        return self._real_type == "String"

    @property
    def _real_type(self):
        if self.is_nullable():
            return self.inner_type
        return self.type_code

    def _infer_inner_type(self):
        if self.is_array():
            return array_type_p.search(self.type_code).groupdict()["inner_type_code"]
        if self.is_nullable():
            return nullable_type_p.search(self.type_code).groupdict()["type_code"]
        if self.is_low_cardinality():
            return low_cardinality_type_p.search(self.type_code).groupdict()["inner_type_code"]
        raise TypeError("No inner type, use type_code instead")

    def cast(self, value):
        if value is None:
            if self.is_string():
                return ""
            else:
                return None

        if self.type_code == "DateTime":
            value = self._convert_datetime(value)
            return str(value)

        if self.type_code == "Date":
            return str(value)
        if self.is_string():
            return value

        if self.is_int() or self.is_float():
            if value == "":
                return 0
            return _clickhouse_type_to_orm_filed[self._real_type].to_python(value, timezone_in_use=None)

        # 处理数组类型
        if self.is_array():
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except Exception:
                    value = []

            if self.inner_type == "DateTime":
                value = str(value)
                value = [self._convert_datetime(x) for x in value]
            inner = _clickhouse_type_to_orm_filed[self.inner_type]
            return fields.ArrayField(inner).to_db_string(value)

        # 其他类型，先不处理，需要的时候再说
        return _clickhouse_type_to_orm_filed[self.type_code].to_db_string(value)

    def _convert_datetime(self, value):
        return str(value)

    def __repr__(self):
        return f"<ClickHouseField({repr(self.name)}, {repr(self.type_code)})>"


@register_connector_class(["clickhouse"])
class ClickHouseConnector(_ShowTableLikeMixin, DBAPIConnector):
    _sqla_driver = "clickhouse"
    _default_port = 8123
    _default_database = "default"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._tcp_port = self.kwargs.get("tcp_port", 9000)
        self._http_port = self.port or self._default_port

    @toolz.memoize
    def connect_impl(self, autocommit=False, *args, **kwargs):
        db_url = f"http://{self.host}:{self.port}"
        return clickhouse.connect(db_name=self.database, db_url=db_url, username=self.user, password=self.password)

    def cursor(self, autocommit=False, dryrun=False, commit_on_close=True, **kwargs):
        if dryrun:
            return NullCursor()
        return WrappedCursor(self.connect(autocommit))

    def is_clickhouse(self):
        return True

    @staticmethod
    def to_canonical_type(type_code, size):
        if "nullable" in type_code.lower():
            type_code = nullable_type_p.search(type_code).groupdict()["inner_type_code"]
        if "lowcardinality" in type_code.lower():
            type_code = low_cardinality_type_p.search(type_code).groupdict()["inner_type_code"]
        if "FixedString" in type_code:
            type_code = "FixedString"
        if "Array" in type_code:
            type_code = "Array"
        return _clickhouse_type_to_canonical_type.get(type_code, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type, size):
        return _canonical_type_to_clickhouse_type.get(canonical_type, "String")

    def generate_create_table_ddl(self, name, schema, **kwargs):
        """从 schema 文件生成建表语句。Table engine 需要从 kwargs 传入，否则默认使用 Log"""
        # Nullable
        cols = []
        for f in schema:
            col_name = self.quote_identifier(f.name)
            if f.comment:
                cols.append(f"{col_name} Nullable({self.from_canonical_type(f.type, f.size)}) COMMENT {f.comment!r}")
            else:
                cols.append(f"{col_name} Nullable({self.from_canonical_type(f.type, f.size)})")

        col_types = ",\n".join(cols)
        name = self.quote_identifier(name)
        ddl = f"CREATE TABLE {name} (\n{col_types}\n)"

        # ddl = super().generate_create_table_ddl(name, schema)

        # Table Engines: https://clickhouse.yandex/docs/en/operations/table_engines/
        engine = kwargs.get("ENGINE", "Log")
        ddl += f" ENGINE = {engine}"
        return ddl

    def load_csv(
        self,
        table,
        filename,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        using_insert=False,
        **kwargs,
    ):
        """Load CSV file to ClickHouse table, support both batch INSERT by Python and clickhouse-client binary"""
        infile = filename
        if skiprows:
            infile = fs.skip_lines(filename, skiprows)

        clickhouse_client_binary = shutil.which("clickhouse-client")
        try_clickhouse_client = (not using_insert) and clickhouse_client_binary
        if try_clickhouse_client:
            self.logger.info("found clickhouse-client in %s, try to load file using it", clickhouse_client_binary)
            self._load_csv_by_clickhouse_client(clickhouse_client_binary, table, filename, delimiter)
        else:
            # fallback to perform INSERT
            self._load_csv_by_inserting(table, filename, delimiter, quotechar, lineterminator, escapechar, **kwargs)

        if infile != filename:
            fs.remove_files_safely(infile)

    def _load_csv_by_clickhouse_client(self, binary, table, filename, delimiter=","):
        if "." not in table:
            table = f"{self.database}.{table}"
        command = " ".join(
            [
                binary,
                f"--host {self.host}",
                f"--port {self._tcp_port}",
                f"--user {self.user}",
                f"--password {self.password}",
                f'--format_csv_delimiter="{delimiter}"',
                f'--query="INSERT INTO {table} FORMAT CSV"' f"< {filename}",
            ]
        )
        self.logger.info(command)
        subprocess.check_call(command, shell=True)

    def _load_csv_by_inserting(self, table, filename, delimiter, quotechar, lineterminator, escapechar, **kwargs):
        # https://clickhouse.yandex/docs/en/query_language/insert_into/
        # Performance Considerations
        # INSERT sorts the input data by primary key and splits them into partitions by a partition key
        # If you insert data into several partitions at once, it can significantly reduce the performance.
        # To avoid this:
        #
        # - Add data in fairly large batches, such as 100,000 rows at a time.
        # - Group data by month before uploading it to ClickHouse.
        batch_size = kwargs.get("batch_size") or 10000

        # https://clickhouse.yandex/docs/en/single/#strong-typing
        columns = self._get_columns_with_type(table)
        values_hook = functools.partial(self._handle_row, columns=columns)
        column_names = [x.name for x in columns]

        self.logger.info("columns: %s", columns)
        self.logger.info("batch size: %s", batch_size)
        self.load_csv_by_inserting(
            table=table,
            filename=filename,
            columns=column_names,
            delimiter=delimiter,
            quotechar=quotechar,
            lineterminator=lineterminator,
            escapechar=escapechar,
            skiprows=0,
            batch_size=batch_size,
            values_hook=values_hook,
            concurrency=kwargs.get("concurrency", 1),
        )

    def _handle_row(self, row, columns):
        rv = []
        for col, value in zip(columns, row):
            rv.append(col.cast(value))
        return tuple(rv)

    def _get_columns_with_type(self, table):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM {}.{} LIMIT 0".format(self.quote_identifier(self.database), self.quote_identifier(table))
            )
            cursor.fetchall()
            cols = [ClickHouseField(x[0], x[1]) for x in cursor.description]
        return cols

    def generate_ddl(self, table, database=None, if_exists=True):
        if database is None:
            database = self.database
        if not self.has_table(table, database):
            raise ValueError(f"Table {table!r} not exists in {database!r}")

        with self.cursor() as cursor:
            cursor.execute(f"SHOW CREATE TABLE {database}.{table}")
            if_exists_stmt = " IF NOT EXISTS " if if_exists else " "
            body = re.search(r"CREATE TABLE (.*)", cursor.fetchall()[0][1], flags=re.S).group(1)
            return f"CREATE TABLE{if_exists_stmt}{body}"
