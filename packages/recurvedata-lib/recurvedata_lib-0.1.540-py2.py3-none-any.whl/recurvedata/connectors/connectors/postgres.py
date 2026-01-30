from functools import cached_property
from typing import Any

from loguru import logger

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.const import ENV_VAR_DBT_PASSWORD, ENV_VAR_DBT_USER
from recurvedata.connectors.datasource import DataSourceWrapper
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "postgres"
UI_CONNECTION_TYPE = "PostgreSQL"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class PostgresConnector(DBAPIBase):
    SYSTEM_DATABASES = [
        "information_schema",
        "pg_catalog",
        "pg_global",
        "pg_statistic",
        "pg_toast",
        "pg_temp_1",
        "pg_temp_2",
        "pg_toast_temp_1",
        "pg_toast_temp_2",
        "pg_type",
    ]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    setup_extras_require = ["psycopg2-binary"]
    driver = "postgresql"
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
                "default": 5432,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
            },
        },
        "order": ["host", "port", "user", "password", "database"],
        "required": [
            "host",
            "user",
            "password",
        ],
        "secret": ["password"],
    }

    column_type_mapping = {
        "integer": ["int2", "int4", "int8", "serial", "bigserial", "smallserial"],
        "float": ["float4", "float8", "real", "numeric", "decimal"],
        "datetime": ["timestamptz"],
        "time": ["timetz"],
        "binary": ["bytea"],
        "string": ["uuid"],
        "json": ["jsonb"],
    }

    # Extend base types with PostgreSQL specific types
    available_column_types = DBAPIBase.available_column_types + [
        # Numeric types
        "int2",  # alias for smallint
        "integer",
        "int4",  # alias for integer
        "int8",  # alias for bigint
        "real",
        "float4",  # alias for real
        "double precision",
        "float8",  # alias for double precision
        "serial",
        "serial4",  # alias for serial
        "bigserial",
        "serial8",  # alias for bigserial
        "smallserial",
        "serial2",  # alias for smallserial
        "money",
        "numeric",
        # Character types
        "text",
        "bpchar",  # blank-padded char
        "character",
        "character varying",
        # Date/Time types
        "timestamp without time zone",
        "timestamp with time zone",
        "timestamptz",  # alias for timestamp with time zone
        "time",
        "time without time zone",
        "time with time zone",
        "timetz",  # alias for time with time zone
        "interval",
        # Boolean type
        "boolean",
        "bool",  # alias for boolean
        # Geometric types
        "point",
        "line",
        "lseg",
        "box",
        "path",
        "polygon",
        "circle",
        # Network address types
        "cidr",
        "inet",
        "macaddr",
        "macaddr8",
        # Binary data
        "bytea",
        # UUID type
        "uuid",
        # JSON types
        "jsonb",
        # XML type
        "xml",
        # Bit string
        "bit",
        "bit varying",
        "varbit",
        # Text search
        "tsvector",
        "tsquery",
        # Range types
        "int4range",
        "int8range",
        "numrange",
        "tsrange",
        "tstzrange",
        "daterange",
    ]

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "user": ENV_VAR_DBT_USER,
            "password": ENV_VAR_DBT_PASSWORD,
            "dbname": database or self.database,
            "schema": schema or f"dbt_{database or self.database}",
            "type": self.connection_type,
        }

    @with_ssh_tunnel
    def get_columns(self, table: str, database: str = None) -> list:
        database = database or self.database
        query = f"""
            WITH table_info AS (
                SELECT c.oid AS table_oid
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = '{database}'
                AND c.relname = '{table}'
            )
            SELECT
                a.attname AS column_name,
                t.typname AS data_type,
                NOT a.attnotnull AS nullable,
                pg_get_expr(ad.adbin, ad.adrelid) AS "default",
                col_description(a.attrelid, a.attnum) AS comment
            FROM pg_attribute a
            JOIN table_info ti ON a.attrelid = ti.table_oid
            JOIN pg_type t ON a.atttypid = t.oid
            LEFT JOIN pg_attrdef ad ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
            WHERE a.attnum > 0
            AND NOT a.attisdropped
            ORDER BY a.attnum;
        """
        result = self.fetchall(query)
        column_metas = []
        for row in result:
            column_metas.append(
                {
                    "name": row[0],
                    "type": row[1].lower() if row[1] else "",
                    "nullable": row[2],
                    "default": row[3],
                    "comment": row[4],
                }
            )
        return column_metas

    @cached_property
    @with_ssh_tunnel
    def type_code_mapping(self) -> dict:
        try:
            rv = self.fetchall("SELECT oid, typname FROM pg_type")
            return {row[0]: row[1] for row in rv if row[1]}
        except Exception:
            pass

    def sqlalchemy_column_type_code_to_name(self, type_code: Any, size: int | None = None) -> str:
        if self.type_code_mapping:
            type_name = self.type_code_mapping.get(type_code)
            if type_name:
                return type_name

        import psycopg2.extensions

        pg_type = psycopg2.extensions.string_types.get(type_code)
        pg_type_name = pg_type.name.lower() if pg_type else None
        if pg_type_name in self.available_column_types:
            return pg_type_name
        return "varchar"

    def convert_config_to_cube_config(
        self, database: str, schema: str = None, datasource: DataSourceWrapper = None
    ) -> dict:
        return {
            "type": "postgres",
            "host": self.host,
            "port": self.port,
            "user": datasource.user,
            "password": datasource.password,
            "database": database or self.database,
        }

    @classmethod
    def convert_normalized_type_to_db_type(cls, normalized_type: str) -> str:
        """
        Convert normalized type to PostgreSQL data type name.
        Maps common normalized types to their preferred PostgreSQL equivalents.
        """
        type_mapping = {
            "integer": "integer",
            "float": "numeric",
            "string": "varchar",
            "boolean": "boolean",
            "date": "date",
            "datetime": "timestamp with time zone",
            "time": "time",
            "binary": "bytea",
            "json": "jsonb",
        }
        _type = type_mapping.get(normalized_type.lower(), normalized_type)
        if not _type:
            logger.warning(f"Unsupported normalized type: {normalized_type}, using varchar as default")
            return "varchar"
        return _type
