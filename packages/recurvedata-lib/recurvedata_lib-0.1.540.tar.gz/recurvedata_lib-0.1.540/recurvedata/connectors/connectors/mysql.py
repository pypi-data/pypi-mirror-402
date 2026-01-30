from functools import cached_property
from typing import Any

from loguru import logger

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.datasource import DataSourceWrapper
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "mysql"
UI_CONNECTION_TYPE = "MySQL"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class MysqlConnector(DBAPIBase):
    SYSTEM_DATABASES = ["information_schema", "mysql", "performance_schema", "sys"]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]

    setup_extras_require = ["pymysql"]
    driver = "mysql+pymysql"
    config_schema = {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "title": _l("Host Address"),
                "default": "127.0.0.1",
            },
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 3306,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
            },
            # 'ssh_tunnel': SSH_TUNNEL_CONFIG_SCHEMA
        },
        "order": [
            "host",
            "port",
            "user",
            "password",
            "database",
        ],
        "required": [
            "host",
        ],
        "secret": ["password"],
    }

    column_type_mapping = {
        "integer": ["mediumint", "year", "long"],
        "string": ["tinytext", "mediumtext", "longtext", "enum", "set", "blob"],
        "binary": ["tinyblob", "mediumblob", "longblob"],
    }

    available_column_types = DBAPIBase.available_column_types + [
        # Integer types
        "tinyint",
        "tinyint unsigned",
        "bit",
        "mediumint",
        "int unsigned",
        "integer",  # alias for int
        "bigint unsigned",
        # Floating-point types
        "numeric",  # alias for decimal
        "fixed",  # alias for decimal
        "double precision",  # alias for double
        "float4",  # alias for float
        "float8",  # alias for double
        # String types
        "tinytext",
        "text",
        "mediumtext",
        "longtext",
        "long",  # alias for mediumtext
        "character",  # alias for char
        "long varchar",  # alias for mediumtext
        "enum",
        "set",
        # Binary string types
        "binary",
        "varbinary",
        "tinyblob",
        "blob",
        "mediumblob",
        "longblob",
        # Date and Time types
        "datetime",
        "time",
        "year",
        # Boolean type
        "bool",  # alias for boolean
    ]

    @with_ssh_tunnel
    def get_columns(self, table, database=None):
        database = database or self.database
        query = f"""
        SELECT column_name,
            data_type,
            is_nullable,
            column_default,
            column_comment
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}';
        """
        result = self.fetchall(query)
        column_metas = []
        for row in result:
            column_metas.append(
                {
                    "name": row[0],
                    "type": row[1].lower() if row[1] else "",
                    "nullable": row[2] == "YES",
                    "default": row[3],
                    "comment": row[4],
                }
            )
        return column_metas

    @cached_property
    @with_ssh_tunnel
    def type_code_mapping(self) -> dict:
        """
        type_code from sqlalchemy's cursor.description -> database's dialect data type name
        """
        return {}

    def sqlalchemy_column_type_code_to_name(self, type_code: Any, size: int | None = None) -> str:
        from pymysql.constants import FIELD_TYPE

        mapping = {type_code: name.lower() for name, type_code in vars(FIELD_TYPE).items() if not name.startswith("__")}
        type_mapping = {
            FIELD_TYPE.TINY: "tinyint",
            FIELD_TYPE.SHORT: "smallint",
            FIELD_TYPE.LONG: "int",
            FIELD_TYPE.LONGLONG: "bigint",
            FIELD_TYPE.INT24: "mediumint",
            FIELD_TYPE.NEWDECIMAL: "decimal",
            FIELD_TYPE.TINY_BLOB: "tinyblob",
            FIELD_TYPE.MEDIUM_BLOB: "mediumblob",
            FIELD_TYPE.LONG_BLOB: "longblob",
            FIELD_TYPE.VAR_STRING: "varchar",
            FIELD_TYPE.STRING: "char",
        }
        return type_mapping.get(type_code, mapping.get(type_code, "varchar"))

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

    def convert_config_to_cube_config(
        self, database: str, schema: str = None, datasource: DataSourceWrapper = None
    ) -> dict:
        return {
            "type": "mysql",
            "host": self.host,
            "port": self.port,
            "user": datasource.user,
            "password": datasource.password,
            "database": database or self.database,
        }

    @classmethod
    def convert_normalized_type_to_db_type(cls, normalized_type: str) -> str:
        """
        Convert normalized type to MySQL data type name.
        Maps common normalized types to their preferred MySQL equivalents.
        """
        default_text_type = "varchar(1024)"
        type_mapping = {
            "integer": "int",
            "float": "double",
            "string": default_text_type,
            "boolean": "bool",
            "date": "date",
            "datetime": "datetime",
            "time": "time",
            "binary": "varbinary(2048)",
            "json": "json",
        }
        _type = type_mapping.get(normalized_type.lower())
        if not _type:
            logger.warning(f"Unsupported normalized type: {normalized_type}, using {default_text_type} as default")
            return default_text_type
        return _type
