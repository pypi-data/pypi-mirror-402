import datetime
import os
import urllib
from collections import OrderedDict

import cytoolz as toolz
import pyodbc

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.azure_blob import AzureBlobConnector
from recurvedata.pigeon.connector.dbapi import DBAPIConnector
from recurvedata.pigeon.schema import types
from recurvedata.pigeon.utils import fs, md5hash, safe_int

# https://github.com/mkleehammer/pyodbc/wiki/Cursor#description
# The 'type code' value is the class type used to create the Python objects when reading rows.
# For example, a varchar column's type will be str.
_mssql_type_to_canonical_type = {
    int: types.INT64,
    float: types.FLOAT64,
    bool: types.BOOLEAN,
    datetime.datetime: types.DATETIME,
    str: types.STRING,
}

_canonical_type_to_mssql_type = {
    types.BOOLEAN: "BIT",
    types.INT8: "TINYINT",
    types.INT16: "SMALLINT",
    types.INT32: "INT",
    types.INT64: "BIGINT",
    types.FLOAT32: "REAL",
    types.FLOAT64: "DOUBLE PRECISION",
    types.DATE: "DATE",
    types.DATETIME: "DATETIME",
    # 使用 NVARCHAR (national character varying) 来支持 unicode
    types.STRING: "NVARCHAR",
    types.JSON: "NVARCHAR",
}


@register_connector_class("mssql")
class SQLServerConnector(DBAPIConnector):
    _sqla_driver = "mssql+pyodbc"
    _identifier_start_quote = "["
    _identifier_end_quote = "]"
    _param_placeholder = "?"
    _default_port = 1433
    _autocommit = False

    def __init__(
        self,
        host=None,
        port=None,
        database=None,
        user=None,
        password=None,
        conn_string=None,
        schema=None,
        odbc_driver: str = "ODBC Driver 18 for SQL Server",
        encrypt: bool = True,
        trust_server_certificate: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(host, port, database, user, password, schema, *args, **kwargs)
        self.odbc_driver = odbc_driver
        self.encrypt = encrypt
        self.trust_server_certificate = trust_server_certificate
        if conn_string:
            attrs = self.parse_conn_string(conn_string)
            for k, v in attrs.items():
                setattr(self, k, v)

    @property
    def conn_string(self):
        # TODO: 使用传进来的 conn string 里相应参数
        options = OrderedDict(
            {
                "Driver": f"{self.odbc_driver}",
                "Server": f"tcp:{self.host},{self.port}",
                "Database": self.database,
                "Uid": self.user,
                "Pwd": "{%s}" % self.password,
                "Encrypt": "yes" if self.encrypt else "no",
                "TrustServerCertificate": "yes" if self.trust_server_certificate else "no",
                "Connection Timeout": 30,
            }
        )
        options.update(self.kwargs.get("odbc_options", {}))
        return ";".join([f"{k}={v}" for k, v in options.items()])

    @staticmethod
    def parse_conn_string(conn_string: str):
        parts = conn_string.strip(";").split(";")
        kvs = {}
        for p in parts:
            k, v = p.split("=")
            kvs[k.lower()] = v

        server = kvs["server"].split(":")[1].split(",")
        return {
            "host": server[0],
            "port": int(server[1]),
            "user": kvs["uid"],
            "password": kvs["pwd"][1:-1],  # remove leading and trailing {}
            "database": kvs["database"],
        }

    def connect_impl(self, autocommit=None, *args, **kwargs):
        if autocommit is None:
            autocommit = self._autocommit
        return pyodbc.connect(self.conn_string, autocommit=autocommit)

    def cursor(self, autocommit=None, dryrun=False, commit_on_close=True, **kwargs):
        if autocommit is None:
            autocommit = self._autocommit
        return super().cursor(autocommit, dryrun, commit_on_close, **kwargs)

    def has_schema(self, schema):
        rv = self.fetchone(f"SELECT * FROM sys.schemas WHERE name='{schema}'")
        return bool(rv)

    def has_table(self, table, schema=None, **kwargs):
        schema, table = self._get_schema_table(table, schema)
        schema = schema or "dbo"
        query = f"""
            SELECT name FROM sys.tables
            WHERE schema_name(schema_id) = '{schema}' AND name = '{table}'
        """
        return bool(self.fetchall(query))

    def create_schema(self, schema):
        with self.cursor() as cursor:
            cursor.execute(f"SELECT * FROM sys.schemas WHERE name='{schema}'")
            exists = bool(cursor.fetchall())
            if not exists:
                cursor.execute(f"CREATE SCHEMA {self.quote_identifier(schema)}")

    def create_master_key(self):
        queries = """
            IF NOT EXISTS (SELECT * FROM sys.symmetric_keys)
            CREATE MASTER KEY
        """
        self.execute(queries)

    def get_columns(self, table, schema=None, exclude=None):
        schema, table = self._get_schema_table(table, schema)
        if not self.has_table(table=table, schema=schema):
            raise ValueError(f"Table {schema}.{table} not exists")

        # the table/view name may be case-sensitive
        query = f"""
            SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS
            WHERE table_schema='{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position
        """
        rv = self.fetchall(query)
        cols = [x[0] for x in rv]
        if exclude:
            cols = [x for x in cols if x not in exclude]
        return cols

    def drop_table_if_exists(self, schema, table, external_table=False):
        schema, table = self._get_schema_table(table, schema)
        external = " EXTERNAL " if external_table else " "
        queries = f"""
          IF EXISTS (
            SELECT * FROM sys.tables WHERE SCHEMA_NAME(schema_id) = '{schema}' AND name = '{table}'
          )
          DROP {external} table {schema}.{table}
        """
        self.execute(queries)

    def load_csv(
        self,
        table,
        filename,
        schema="dbo",
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        using_insert=None,
        **kwargs,
    ):
        if not using_insert:
            try:
                options = dict(
                    columns=columns,
                    delimiter=delimiter,
                    quotechar=quotechar,
                    lineterminator=lineterminator,
                    escapechar=escapechar,
                    skiprows=skiprows,
                )
                options.update(**kwargs)
                self.load_csv_bulk(table, filename, schema, **options)
            except Exception as e:
                self.logger.warning("bulk load local file is not supported, apply INSERT instead. error: %s", e)
            else:
                return

        # SQL Server 有参数数量限制
        # https://docs.microsoft.com/en-us/sql/sql-server/maximum-capacity-specifications-for-sql-server
        num_params_limit = 2100 - 1
        if not columns:
            columns = self.get_columns(table=table, schema=schema)

        batch_size = kwargs.get("batch_size", 1000)
        new_batch_size = int(min(num_params_limit / len(columns), batch_size))
        self.logger.info(
            "table has %s columns, adjust batch_size from %s to %s", len(columns), batch_size, new_batch_size
        )
        kwargs["batch_size"] = new_batch_size

        table = self._format_table_name(table, schema)
        self.load_csv_by_inserting(
            table, filename, columns, delimiter, quotechar, lineterminator, escapechar, skiprows, **kwargs
        )

    def load_csv_bulk(
        self,
        table,
        filename,
        schema="dbo",
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        **kwargs,
    ):
        raise NotImplementedError

    def _format_table_name(self, table, schema):
        if schema and "." not in table:
            table = self.quote_identifier(f"{schema}.{table}")
        return table

    def _get_schema_table(self, table, schema):
        if "." in table:
            schema, table = table.split(".")
        if not schema:
            schema = "dbo"
        return schema, table

    @staticmethod
    def to_canonical_type(type_code, size):
        return _mssql_type_to_canonical_type.get(type_code, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type, size):
        if canonical_type == types.STRING:
            # 使用 4 个字节表示一个字符比较安全
            # https://docs.microsoft.com/en-us/sql/t-sql/data-types/nchar-and-nvarchar-transact-sql?view=sql-server-2017#arguments
            # max indicates that the maximum storage size is 2^30-1 characters
            size = safe_int(size) * 4
            if size > 4000:
                size = "max"
            elif size == 0:
                size = "max"
            mssql_type = f"NVARCHAR({size})"
        else:
            mssql_type = _canonical_type_to_mssql_type.get(canonical_type, "NVARCHAR(200)")
        return mssql_type

    def generate_ddl(self, table, schema="dbo", database=None, if_exists=True):
        schema, table = self._get_schema_table(table, schema)
        if not self.has_table(table, schema):
            raise ValueError(f"Table {table!r} not exists in {database!r}")

        query = f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE table_schema = '{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position
        """
        with self.cursor() as cursor:
            cursor.execute(query)
            columns = cursor.fetchall()

        col_definitions = []
        # column_name, data_type, character_maximum_length, is_nullable
        for col in columns:
            dtype = col.data_type
            if col.character_maximum_length:
                dtype = f"{dtype}({col.character_maximum_length})"
            null_modifier = "DEFAULT" if col.is_nullable == "YES" else "NOT"
            definition = f"[{col.column_name}] {dtype.upper()} {null_modifier} NULL"
            col_definitions.append(definition)

        body = ",\n\t\t\t\t".join(col_definitions)
        ddl = f"""
            CREATE TABLE [{schema}].[{table}] (
                {body}
            )
        """
        if if_exists:
            ddl = f"""
            IF NOT EXISTS (
                SELECT * FROM sys.tables
                WHERE schema_name(schema_id) = '{schema}' AND name = '{table}'
            )
            {ddl}
            """
        return ddl

    def is_mssql(self):
        return True

    def _get_sqlalchemy_uri(self):
        return "mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(self.conn_string)


# 兼容老代码
MSSQLConnector = SQLServerConnector


class BaseAzureSQLConnector(SQLServerConnector):
    """Base class for Azure SQL based connectors (Synapse and Fabric)
    Provides common functionality for Azure SQL services
    reference:
        - https://learn.microsoft.com/en-us/sql/t-sql/statements/copy-into-transact-sql?view=fabric
        - https://learn.microsoft.com/en-us/sql/t-sql/statements/copy-into-transact-sql?view=azure-sqldw-latest
    """

    def _get_credential(self, blob: AzureBlobConnector) -> str:
        """Get Azure Blob Storage credential for COPY INTO command.

        Args:
            blob: Azure Blob Storage connector instance

        Returns:
            str: Credential string for COPY INTO command
        """
        if blob.account_key:
            return f"CREDENTIAL=(IDENTITY= 'Storage Account Key', SECRET='{blob.account_key}'),"
        elif blob.sas_token:
            return f"CREDENTIAL=(IDENTITY= 'Shared Access Signature', SECRET='{blob.sas_token}'),"
        else:
            return ""

    def load_csv_bulk(
        self,
        table: str,
        filename: str,
        schema="dbo",
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        **kwargs,
    ):
        """
        Bulk load data using COPY command for Azure SQL services

        Args:
            table: Target table name
            filename: Source file path
            schema: Schema name
            columns: List of column names
            delimiter: Field delimiter
            quotechar: Quote character
            lineterminator: Line terminator
            escapechar: Escape character
            skiprows: Number of rows to skip
            **kwargs: Additional arguments
        """
        blob = self.create_blob_connector()
        if not blob:
            raise RuntimeError("blob storage is not configured")

        # upload
        if filename.endswith(".gz"):
            file_to_upload = filename
        else:
            self.logger.info("compressing file %s", filename)
            file_to_upload = fs.gzip_compress(filename, using_cmd=True)

        if "." in table:
            schema, table = table.split(".")

        container = self.kwargs.get("blob_options", {}).get("container_name", self._generate_blob_container_name())
        blob.create_container(container)
        blob_name = f"{self.database}/{schema}/{table}/{os.path.basename(file_to_upload)}"
        self.logger.info(f"uploading {file_to_upload} to {container}/{blob_name}")
        blob_path = blob.upload(container, file_to_upload, blob_name)

        if columns:
            column_list = f'({", ".join(columns)})'
        else:
            column_list = ""

        query = f"""
            COPY INTO {self.quote_identifier(schema)}.{self.quote_identifier(table)} {column_list}
            FROM '{blob.get_url(container, blob_name)}'
            WITH (
                FILE_TYPE = 'CSV',
                {self._get_credential(blob)}
                COMPRESSION = 'Gzip',
                FIELDQUOTE = '{quotechar}',
                FIELDTERMINATOR = '{delimiter}',
                ROWTERMINATOR = '{lineterminator}',
                FIRSTROW = {skiprows + 1}
            )
            OPTION (LABEL = 'COPY {schema}.{table}')
        """
        try:
            self.logger.info("running COPY command")
            self.execute(query, autocommit=False, commit_on_close=True)
            self.logger.info("COPY finished")
        except Exception as e:
            self.logger.exception("failed to copy data to database")
            raise e
        finally:
            if file_to_upload != filename:
                self.logger.info("delete %s", file_to_upload)
                fs.remove_files_safely(file_to_upload)

            self.logger.info(f"delete blob: {blob_path}")
            try:
                blob.delete_blob(container, blob_name)
            except Exception as e:
                self.logger.error(f"operation on blob storage fails: {e}")

    @toolz.memoize
    def create_blob_connector(self):
        """Create blob connector"""
        blob_options = self.kwargs.get("blob_options")
        if not blob_options:
            return None
        return AzureBlobConnector(**blob_options)

    def _generate_blob_container_name(self):
        """Generate blob container name that follows Azure naming rules:
        - 3-63 characters long
        - Lowercase letters, numbers, and hyphens only
        - Must start and end with a letter or number
        - No consecutive hyphens
        """
        # Get instance name and limit its length to 20 characters
        instance = self.host.split(".", 1)[0][:20]
        # Remove any non-alphanumeric characters and convert to lowercase
        instance = "".join(c for c in instance if c.isalnum()).lower()
        # Ensure instance is not empty
        if not instance:
            instance = "default"
        # Generate container name with fixed prefix and limited length
        container_name = f"pigeon-{instance}-{md5hash(self.host)[:8]}"
        # Ensure total length is within limits (63 chars)
        if len(container_name) > 63:
            container_name = container_name[:63]
        # Ensure name ends with alphanumeric
        while not container_name[-1].isalnum():
            container_name = container_name[:-1]
        return container_name


@register_connector_class("azure_mssql")
class AzureSQLServerConnector(BaseAzureSQLConnector):
    pass
