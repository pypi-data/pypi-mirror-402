# description : use clickhouse-driver [https://github.com/mymarilyn/clickhouse-driver]

import datetime
import functools
import json
import re
import shutil
import subprocess

import clickhouse_driver

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.dbapi import DBAPIConnector
from recurvedata.pigeon.schema import types
from recurvedata.pigeon.utils import fs

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

nullable_type_p = re.compile(r"Nullable\((?P<inner_type_code>.*)\)")
array_type_p = re.compile(r"Array\((?P<inner_type_code>.*)\)")
low_cardinality_type_p = re.compile(r"LowCardinality\((?P<inner_type_code>.*)\)")


@register_connector_class(["clickhouse_native", "clickhouse"])
class ClickHouseConnector(DBAPIConnector):
    _sqla_driver = "clickhouse+native"
    _default_port = 9000
    _default_database = "default"

    def is_clickhouse_native(self):
        return True

    def connect_impl(self, autocommit=False, *args, **kwargs):
        conn_kwargs = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "compression": True,
        }
        conn_kwargs.update(self.kwargs)
        conn_kwargs.update(kwargs)
        return clickhouse_driver.connect(**conn_kwargs)

    def cursor(self, autocommit=False, dryrun=False, commit_on_close=True, stream=False, max_rows=0, **kwargs):
        """Returns a clickhouse DBAPI cursor
        stream: enable or disable results streaming
        max_rows: specifies the maximum number of rows to buffer at a time
        """
        ch_cursor = super().cursor(autocommit=autocommit, dryrun=dryrun, commit_on_close=commit_on_close, **kwargs)
        if stream:
            ch_cursor._cursor.set_stream_results(stream_results=stream, max_row_buffer=max_rows)
        return ch_cursor

    def has_table(self, table, database=None, **kwargs) -> bool:
        # check if table exists: https://clickhouse.com/docs/en/sql-reference/statements/exists/
        database = database or self.database
        rows = self.fetchall(f"EXISTS `{database}`.`{table}`")
        return bool(rows[0][0])

    def get_columns(self, table, database=None, exclude=None):
        database = database or self.database
        if not self.has_table(table, database):
            raise ValueError("Table {!r} not exists in {!r}".format(table, database))
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM {}.{} LIMIT 0".format(self.quote_identifier(database), self.quote_identifier(table))
            )
            cols = [x.name for x in cursor.description if x not in (exclude or ())]
        return cols

    def generate_ddl(self, table, database=None, if_exists=True):
        database = database or self.database
        if not self.has_table(table, database):
            raise ValueError(f"Table {table!r} not exists in {database!r}")

        with self.cursor() as cursor:
            cursor.execute(f"SHOW CREATE TABLE {self.quote_identifier(database)}.{self.quote_identifier(table)}")
            if_exists_stmt = " IF NOT EXISTS " if if_exists else " "
            body = re.search(r"CREATE TABLE (.*)", cursor.fetchall()[0][0], flags=re.S).group(1)
            return f"CREATE TABLE{if_exists_stmt}{body}"

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
            cols = [ClickHouseField(x.name, x.type_code) for x in cursor.description]
        return cols

    def _bulk_insert(self, cursor, table, cols, rows):
        if not rows:
            return
        if cols:
            field_names = "({})".format(", ".join([self.quote_identifier(x) for x in cols]))
        else:
            field_names = ""
        sql = f"INSERT INTO {table} {field_names} VALUES"
        cursor.executemany(sql, rows)
        cursor.connection.commit()

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
                f"--port {self.port}",
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


class ClickHouseField:
    """将 clickhouse datatype 转换成 python datatype"""

    def __init__(self, name, type_code):
        self.name = name
        self.type_code = type_code

        if self.is_array() or self.is_nullable() or self.is_low_cardinality():
            self.inner_type = self._infer_inner_type()
        else:
            self.inner_type = None

    @classmethod
    def get_converters(cls, columns_with_type: dict):
        return {name: cls(type_code) for name, type_code in columns_with_type.items()}

    def is_array(self):
        return self.type_code.startswith("Array")

    def is_nullable(self):
        return self.type_code.startswith("Nullable")

    def is_low_cardinality(self):
        return self.type_code.startswith("LowCardinality")

    @property
    def _real_type(self):
        if self.is_nullable():
            return self.inner_type
        return self.type_code

    def is_int(self):
        return self._real_type in ["UInt8", "UInt16", "UInt32", "UInt64", "Int8", "Int16", "Int32", "Int64"]

    def is_float(self):
        return self._real_type in ["Float32", "Float64"]

    def is_string(self):
        return self._real_type == "String"

    def _infer_inner_type(self):
        for f, p in [
            (self.is_array, array_type_p),
            (self.is_nullable, nullable_type_p),
            (self.is_low_cardinality, low_cardinality_type_p),
        ]:
            if f():
                return p.search(self.type_code).groupdict()["inner_type_code"]
        raise TypeError("No inner type, use type_code instead")

    def _convert_datetime(self, value, type_code):
        if type_code == "DateTime":
            return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()

    def cast(self, value):
        if value is None:
            if self.is_string():
                return ""
            else:
                return None

        if self.type_code in ("DateTime", "Date"):
            return self._convert_datetime(value, self.type_code)

        if self.is_string():
            return value

        if self.is_int() or self.is_float():
            if value == "":
                return 0
            if self.is_int():
                return int(value)
            else:
                return float(value)

        # 处理数组类型
        if self.is_array():
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except Exception:
                    value = []

            if self.inner_type == "DateTime":
                value = [self._convert_datetime(x, self.inner_type) for x in value]
            return value

        # 其他类型，先不处理，需要的时候再说
        return value

    def __repr__(self):
        return f"<ClickHouseField({repr(self.name)}, {repr(self.type_code)})>"
