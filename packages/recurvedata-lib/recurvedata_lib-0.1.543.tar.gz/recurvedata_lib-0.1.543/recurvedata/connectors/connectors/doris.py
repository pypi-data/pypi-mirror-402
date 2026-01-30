from functools import cached_property
from typing import Any

from loguru import logger

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.const import ENV_VAR_DBT_PASSWORD, ENV_VAR_DBT_USER, SSH_TUNNEL_CONFIG_SCHEMA
from recurvedata.connectors.datasource import DataSourceWrapper
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l
from recurvedata.executors.schemas import ColumnItem

CONNECTION_TYPE = "doris"
UI_CONNECTION_TYPE = "SelectDB(Doris)"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class ApacheDorisConnector(DBAPIBase):
    SYSTEM_DATABASES = [
        "information_schema",
        "mysql",
        "__internal_schema",
    ]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = ["sqlalchemy-doris[pymysql]"]
    driver = "doris+pymysql"
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "title": _l("Host Address"),
                "default": "127.0.0.1",
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
            },
            "port": {
                "type": "number",
                "title": _l("SelectDB(Doris) Port Number"),
                "description": _l("The port number for connecting to SelectDB(Doris) server on FE"),
                "default": 9030,
            },
            "http_port": {
                "type": "number",
                "title": _l("FE HTTP Port"),
                "description": _l("The HTTP port number for the Doris Frontend (FE) service"),
                "default": 8030,
            },
            "ssh_tunnel": SSH_TUNNEL_CONFIG_SCHEMA,
        },
        "order": ["host", "port", "http_port", "user", "password", "database", "ssh_tunnel"],
        "required": ["host", "http_port"],
        "secret": ["password"],
    }

    available_column_types = DBAPIBase.available_column_types + [
        # Numeric types
        "tinyint",
        "integer",  # alias for int
        "largeint",  # 128-bit signed integer
        "numeric",  # alias for decimal
        "real",  # alias for float
        "double precision",  # alias for double
        "bigint unsigned",
        # String types
        "text",  # alias for string
        "string",  # alias for varchar
        # Date and Time types
        "datetime",  # alias for timestamp
        "time",
        # Complex types
        "array",
        "map",
        "struct",
        "variant",
        "json",
        # Special types
        "bitmap",
        "hll",
        "quantile_state",
        "agg_state",
        # Boolean type
        "boolean",
        "bool",  # alias for
        # IP types
        "ipv4",
        "ipv6",
    ]

    column_type_mapping = {
        "integer": ["tinyint", "largeint"],
        "string": ["text", "string"],
    }

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "username": ENV_VAR_DBT_USER,
            "password": ENV_VAR_DBT_PASSWORD,
            "schema": database or self.database,
            "type": "doris",
            "threads": 10,
        }

    @with_ssh_tunnel
    def get_tables(self, database: str = None) -> list[str]:
        # todo: update doris inspector in sqlalchemy-doris, which return both views and tables
        table_views: list[str] = super().get_tables(database)
        for view in self.get_views(database):
            if view in table_views:
                table_views.remove(view)
        return table_views

    @with_ssh_tunnel
    def get_columns(self, table: str, database: str = None) -> list:
        database = database or self.database
        query = f"""
                SELECT
                    column_name,
                    data_type,
                    column_default,
                    is_nullable,
                    column_comment
                FROM information_schema.columns
                WHERE table_schema = '{database}'
                AND table_name = '{table}'
                """
        column_metas = []
        results = self.fetchall(query)
        for row in results:
            column_metas.append(
                {
                    "name": row[0],
                    "type": row[1].lower() if row[1] else "",
                    "default": row[2],
                    "nullable": row[3] == "YES",
                    "comment": row[4],
                }
            )

        return column_metas

    @cached_property
    @with_ssh_tunnel
    def type_code_mapping(self) -> dict:
        query = "SHOW DATA TYPES"
        rv = self.fetchall(query)
        return {row[0]: row[0] for row in rv}

    def sqlalchemy_column_type_code_to_name(self, type_code: Any, size: int | None = None) -> str:
        # values refer to https://doris.apache.org/docs/table-design/data-type/
        # values of this mapping must be in available_column_types, or just default as string
        from pymysql.constants import FIELD_TYPE

        type_code_mapping = {
            FIELD_TYPE.TINY: "tinyint",
            FIELD_TYPE.SHORT: "smallint",
            FIELD_TYPE.LONG: "int",
            FIELD_TYPE.FLOAT: "float",
            FIELD_TYPE.DOUBLE: "double",
            FIELD_TYPE.DECIMAL: "decimal",
            FIELD_TYPE.NEWDECIMAL: "decimal",
            FIELD_TYPE.LONGLONG: "bigint",
            FIELD_TYPE.INT24: "int",
            FIELD_TYPE.DATE: "date",
            FIELD_TYPE.NEWDATE: "date",
            FIELD_TYPE.DATETIME: "datetime",
            FIELD_TYPE.STRING: "varchar",
            FIELD_TYPE.VARCHAR: "varchar",
            FIELD_TYPE.JSON: "json",
        }
        return type_code_mapping.get(type_code, "varchar")

    def convert_config_to_cube_config(
        self, database: str, schema: str = None, datasource: DataSourceWrapper = None
    ) -> dict:
        return {
            "type": "doris",
            "host": self.host,
            "port": self.port,
            "user": datasource.user,
            "password": datasource.password,
            "database": database or self.database,
        }

    @classmethod
    def order_sql(cls, sql: str, orders: list[dict[str, str]] = None):
        base_sql = f"SELECT * FROM ({sql}) AS _recurve_limit_subquery"
        if orders:
            order_clauses = [f"{order['field']} {order['order']}" for order in orders]
            base_sql += " ORDER BY " + ", ".join(order_clauses)
        return base_sql

    @classmethod
    def limit_sql(cls, sql: str, limit: int = 100, orders: list[dict[str, str]] | None = None, offset: int = 0) -> str:
        """
        the sqlglot will convert `timestamp` to `datetime`,
        which cause this sql: `cast(field as timestamp) as field` to be error in dbt build but success in preview.
        args:
            sql: the sql to be limited
            limit: the limit of the sql
            orders: the orders of the sql(list[dict[str, str]]), each dict contains `field` and `order`, used in data service preview
        """
        base_sql = cls.order_sql(sql, orders)
        if offset:
            return f"{base_sql} LIMIT {offset}, {limit}"

        return f"{base_sql} LIMIT {limit}"

    @classmethod
    def create_table_sql(
        cls,
        table: str,
        columns: list[ColumnItem],
        keys: list[str] = None,
        database: str = None,
        schema: str = None,
        if_not_exists: bool = True,
        **kwargs,
    ) -> str:
        """
        Generate CREATE TABLE DDL
        Args:
            table: str, the name of the table
            columns: list[ColumnItem], the columns of the table
            keys: list[str], the keys of the table
            database: str, the database of the table
            schema: str, the schema of the table
            if_not_exists: bool, whether to create the table if it doesn't exist
            **kwargs: dict, the extra arguments of the table
            - properties: dict, the properties of the table
        """
        if database:
            table = f"{database}.{table}"

        _columns = []
        for column in columns:
            ctype = cls.convert_normalized_type_to_db_type(column.normalized_type)
            _columns.append(f"{column.name} {ctype}")

        sql = "CREATE TABLE"
        if if_not_exists:
            sql += " IF NOT EXISTS"
        sql += f" {table} ({', '.join(_columns)}) ENGINE=OLAP"
        if keys:
            keys_str = ", ".join(keys)
            sql += f"\nUNIQUE KEY ({keys_str})"
            sql += f"\nDISTRIBUTED BY HASH({keys_str}) BUCKETS 1"

        properties = kwargs.get("properties")
        if properties:
            properties_str = ", ".join([f"{key} = {value}" for key, value in properties.items()])
            sql += f"\nPROPERTIES ({properties_str})"

        return sql

    @classmethod
    def convert_normalized_type_to_db_type(cls, normalized_type: str) -> str:
        """
        Convert normalized type to Doris data type name.
        Maps common normalized types to their preferred Doris equivalents.
        """
        default_text_type = "varchar(1024)"
        type_mapping = {
            "integer": "int",
            "float": "decimal",
            "string": default_text_type,
            "boolean": "boolean",
            "date": "date",
            "datetime": "datetime",
            "time": "datetime",
            "binary": default_text_type,
            "json": "json",
        }
        _type = type_mapping.get(normalized_type.lower())
        if not _type:
            logger.warning(f"Unsupported normalized type: {normalized_type}, using {default_text_type} as default")
            return default_text_type
        return _type
