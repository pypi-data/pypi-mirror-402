from functools import cached_property
from typing import Any

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.const import ENV_VAR_DBT_PASSWORD, ENV_VAR_DBT_USER
from recurvedata.connectors.datasource import DataSourceWrapper
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "redshift"
UI_CONNECTION_TYPE = "Redshift"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class RedshiftConnector(DBAPIBase):
    SYSTEM_DATABASES = ["information_schema", "pg_catalog", "public", "temporary"]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    driver = "redshift+psycopg2"
    setup_extras_require = ["psycopg2-binary", "sqlalchemy_redshift==0.8.15+recurve"]
    config_schema = {
        "type": "object",
        "properties": {
            "host": {"type": "string", "title": _l("Host Address")},
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 5439,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
            },
            "s3_options": {
                "type": "object",
                "title": _l("S3 Configuration"),
                "description": _l("AWS S3 credentials for data loading and unloading"),
                "properties": {
                    "access_key_id": {"type": "string", "title": _l("AWS Access Key ID")},
                    "secret_access_key": {"type": "string", "title": _l("AWS Secret Access Key")},
                    "region": {"type": "string", "title": _l("AWS Region")},
                },
                "order": ["access_key_id", "secret_access_key", "region"],
            },
        },
        "order": ["host", "port", "user", "password", "database", "s3_options"],
        "required": ["host", "port"],
        "secret": ["password"],
    }

    # All supported Redshift data types based on official documentation
    available_column_types = [
        # Numeric types
        "smallint",
        "int2",
        "integer",
        "int",
        "int4",
        "bigint",
        "int8",
        "decimal",
        "numeric",
        "real",
        "float",
        "float4",
        "double precision",
        "float8",
        # Character types
        "char",
        "character",
        "nchar",
        "bpchar",
        "varchar",
        "character varying",
        "nvarchar",
        "text",
        # Datetime types
        "date",
        "timestamp",
        "timestamptz",
        "timestamp with time zone",
        "timestamp without time zone",
        "time",
        "timetz",
        "time with time zone",
        "time without time zone",
        # Boolean type
        "boolean",
        "bool",
        # Special types
        "super",
        "hllsketch",
        "geometry",
        "geography",
        "varbyte",
    ]

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "user": ENV_VAR_DBT_USER,
            "password": ENV_VAR_DBT_PASSWORD,
            "dbname": database,
            "schema": schema,
            "type": self.connection_type,
            "threads": 10,
        }

    @with_ssh_tunnel
    def get_columns(self, table: str, database=None):
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
            rv = self.fetchall("SELECT oid, typname FROM pg_catalog.pg_type")
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
            "type": "redshift",
            "host": self.host,
            "port": self.port,
            "user": datasource.user,
            "password": datasource.password,
            "database": database or self.database,
        }
