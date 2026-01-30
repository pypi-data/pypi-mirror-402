import psycopg2

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.dbapi import ClosingCursor, DBAPIConnector, NullCursor
from recurvedata.pigeon.schema import types

_pg_type_to_canonical_type = {
    16: types.BOOLEAN,
    21: types.INT16,
    23: types.INT32,
    20: types.INT64,
    114: types.JSON,
    700: types.FLOAT32,
    701: types.FLOAT64,
    1700: types.FLOAT64,
    1114: types.DATETIME,
    1184: types.DATETIME,
    1082: types.DATE,
    1043: types.STRING,
    1014: types.STRING,
    1015: types.STRING,
    1008: types.STRING,
    1009: types.STRING,
    2951: types.STRING,
}

canonical_type_to_pg_type = {
    types.BOOLEAN: "BOOLEAN",
    types.INT8: "INT2",
    types.INT16: "INT2",
    types.INT32: "INT4",
    types.INT64: "INT8",
    types.FLOAT32: "FLOAT4",
    types.FLOAT64: "FLOAT8",
    types.DATETIME: "TIMESTAMP",
    types.DATE: "DATE",
    types.STRING: "TEXT",
    types.JSON: "JSON",
}


class NamedCursor(ClosingCursor):
    """NamedCursor is a server side cursor, using DECLARE and FETCH internally
    http://initd.org/psycopg/docs/usage.html#server-side-cursors
    """

    def __init__(self, connection, commit_on_close=True, name=None):
        self.connection = connection
        self._commit_on_close = commit_on_close
        if name is not None:
            self._cursor = connection.cursor(name, withhold=True)
            self._cursor.itersize = 1000
        else:
            self._cursor = connection.cursor()


@register_connector_class(["postgres", "postgresql"])
class PostgresConnector(DBAPIConnector):
    _sqla_driver = "postgresql+psycopg2"
    _identifier_start_quote = '"'
    _identifier_end_quote = '"'
    _default_port = 5432

    def connect_impl(self, autocommit=False, *args, **kwargs):
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            *args,
            **kwargs,
        )
        conn.autocommit = autocommit

        if self.schema:
            with conn.cursor() as cursor:
                cursor.execute(f"SET search_path TO {self.schema}, public")

        return conn

    def cursor(self, autocommit=False, dryrun=False, commit_on_close=True, **kwargs):
        """Returns a DBAPI cursor"""
        if dryrun:
            return NullCursor()
        cursor_name = kwargs.pop("cursor_name", None)
        conn = self.connect(autocommit, **kwargs)
        return NamedCursor(conn, commit_on_close=commit_on_close, name=cursor_name)

    def has_table(self, table, database=None, schema="public", **kwargs):
        schema, table = self._get_schema_table(table, schema)

        if database is not None and database != self.database:
            conn = self.clone()
            conn.database = database
        else:
            conn = self
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.tables
                  WHERE table_name = %s AND table_schema = %s
                )
            """,
                (table, schema),
            )
            return bool(cursor.fetchone()[0])

    def get_columns(self, table, schema="public", database=None):
        schema, table = self._get_schema_table(table, schema)
        if database is None:
            database = self.database
        if not self.has_table(table, database, schema=schema):
            raise ValueError("Table {!r}.{!r} not exists in {!r}".format(schema, table, database))
        with self.cursor() as cursor:
            cursor.execute('SELECT * FROM "{}"."{}" LIMIT 0'.format(schema, table))
            cursor.fetchall()
            return [x[0] for x in cursor.description]

    def generate_ddl(self, table, schema="public", database=None, field_filter=(), if_exists=True):
        schema, table = self._get_schema_table(table, schema)
        if database is None:
            database = self.database
        if not self.has_table(table, database, schema=schema):
            raise ValueError(f"Table {schema!r}.{table!r} not exists in {database!r}")

        with self.cursor() as cursor:
            # get table comment
            tbl_comment_sql = f"""
            SELECT pgd.description AS table_comment
            FROM pg_catalog.pg_description pgd
            WHERE pgd.objsubid = 0 AND pgd.objoid = (SELECT c.oid
                                                     FROM pg_catalog.pg_class c
                                                         LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                                                     WHERE n.nspname = {schema!r}
                                                           AND c.relname = {table!r} AND
                                                           c.relkind IN ('r', 'v', 'm', 'f'));
            """
            cursor.execute(tbl_comment_sql)
            t_comment = cursor.fetchall()
            # get columns
            col_comment_sql = f"""
            SELECT
                a.attname                                       AS "field",
                pg_catalog.format_type(a.atttypid, a.atttypmod) AS "type",
                (SELECT pg_catalog.pg_get_expr(d.adbin, d.adrelid)
                 FROM pg_catalog.pg_attrdef d
                 WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum
                       AND a.atthasdef)
                                                                AS "default",
                a.attnotnull                                    AS "isnull",
                pgd.description                                 AS "comment"
            FROM pg_catalog.pg_attribute a
                LEFT JOIN pg_catalog.pg_description pgd ON (
                    pgd.objoid = a.attrelid AND pgd.objsubid = a.attnum)
            WHERE a.attrelid = (SELECT c.oid
                                FROM pg_catalog.pg_class c
                                    LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                                WHERE n.nspname = {schema!r}
                                      AND c.relname = {table!r} AND c.relkind IN ('r', 'v', 'm', 'f'))
                  AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum;
            """
            cursor.execute(col_comment_sql)
            col_info = cursor.fetchall()

        if t_comment:
            comments = [f"COMMENT ON TABLE {self.quote_identifier(table)} IS {t_comment[0][0]!r};"]
        else:
            comments = []

        cols = []
        for col in col_info:
            if col in field_filter:
                continue
            default = " DEFAULT {col[2]}" if col[2] else ""
            isnull = " NOT NULL " if col[3] else ""
            if "character varying" in col[1]:
                ctype = col[1].replace("character varying", "varchar")
                cols.append(f"{self.quote_identifier(col[0])} {ctype}{isnull}{default}")
            else:
                cols.append(f"{self.quote_identifier(col[0])} {col[1]}{isnull}{default}")
            if col[4]:
                comments.append(
                    f"COMMENT ON COLUMN {self.quote_identifier(table)}.{self.quote_identifier(col[0])} IS {col[4]!r};"
                )
        if_exists_stmt = " IF NOT EXISTS " if if_exists else " "
        cols_stmt = ", ".join(cols)
        comments_stmt = " ".join(comments)
        return f"CREATE TABLE{if_exists_stmt}{self.quote_identifier(table)} ({cols_stmt}); {comments_stmt}"

    def is_postgres(self):
        return True

    @staticmethod
    def to_canonical_type(type_code, size):
        return _pg_type_to_canonical_type.get(type_code, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type, size):
        return canonical_type_to_pg_type.get(canonical_type, "TEXT")

    def load_csv(
        self,
        table,
        filename,
        schema="public",
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        using_insert=True,
        **kwargs,
    ):
        # if using_insert:
        #     method = self.load_csv_by_inserting
        # else:
        #     method = self._copy_csv
        if not using_insert:
            self.logger.warning("load file directly is not implemented yet, fallback to using bulk INSERT")

        method = self.load_csv_by_inserting
        schema, table = self._get_schema_table(table, schema)
        table = self._format_table_name(table, schema)

        return method(
            table, filename, columns, delimiter, quotechar, lineterminator, escapechar, skiprows=skiprows, **kwargs
        )

    def _copy_csv(
        self,
        table,
        filename,
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        **kwargs,
    ):
        conn = self.connect()
        cursor = conn.cursor()
        self.logger.info("copy file %s into %s", filename, table)
        with open(filename, "r") as f:
            if skiprows:
                for _ in range(skiprows):
                    f.readline()
            # the copy_from method does support standard CSV
            cursor.copy_from(f, table, sep=delimiter, columns=columns)
        conn.commit()
        conn.close()

    def _get_schema_table(self, table, schema):
        if "." in table:
            schema, table = table.split(".")
        if not schema:
            schema = "public"
        return schema, table

    def _format_table_name(self, table, schema):
        if schema and "." not in table:
            table = self.quote_identifier(f"{schema}.{table}")
        return table
