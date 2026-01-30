import base64
import json
import os
from functools import cached_property
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.datasource import DataSourceWrapper
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.connectors.proxy import HTTP_PROXY_CONFIG_SCHEMA, HttpProxyMixin
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "bigquery"
UI_CONNECTION_TYPE = "Google BigQuery"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class BigQueryConnector(HttpProxyMixin, DBAPIBase):
    setup_extras_require = ["sqlalchemy-bigquery"]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    driver = "bigquery"
    category = [
        ConnectionCategory.WAREHOUSE,
        ConnectionCategory.DATABASE,
    ]
    group = [ConnectorGroup.DESTINATION]

    # All supported BigQuery data types and their aliases based on official documentation
    available_column_types = [
        # Integer types
        "int64",  # 64-bit integer
        "integer",  # alias for int64
        "int",  # alias for int64
        "smallint",  # alias for int64
        "bigint",  # alias for int64
        "tinyint",  # alias for int64
        "byteint",  # alias for int64
        # Floating-point types
        "float64",  # 64-bit floating point
        # Decimal types
        "numeric",  # exact numeric values
        "decimal",  # alias for numeric
        "bignumeric",  # high-precision decimal values
        "bigdecimal",  # alias for bignumeric
        # String type
        "string",  # variable-length character data
        # Boolean type
        "bool",  # true or false
        "boolean",  # alias for bool
        # Bytes type
        "bytes",  # variable-length binary data
        # Date/Time types
        "date",  # calendar date
        "datetime",  # date and time
        "time",  # time of day
        "timestamp",  # absolute point in time
        # Complex types
        "array",  # ordered list of values
        "struct",  # container of ordered fields
        "json",
        # Geography type
        "geography",  # spatial data type
        # Interval type
        "interval",  # time intervals
        # Range types
        "range",
    ]

    config_schema = {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "title": _l("Account Type"),
                "default": "service_account",
            },
            "project_id": {"type": "string", "title": _l("Google Cloud Project ID")},
            "private_key_id": {"type": "string", "title": _l("Google Auth Private Key ID")},
            "private_key": {"type": "string", "title": _l("Google Auth Private Key")},
            "client_id": {"type": "string", "title": _l("Google OAuth Client ID")},
            "client_email": {"type": "string", "title": _l("Service Account Email")},
            "token_uri": {
                "type": "string",
                "title": _l("Google OAuth Token URI"),
                "default": "https://oauth2.googleapis.com/token",
            },
            "proxies": HTTP_PROXY_CONFIG_SCHEMA["proxies"],
        },
        "order": [
            "type",
            "project_id",
            "private_key_id",
            "private_key",
            "client_id",
            "client_email",
            "token_uri",
            "proxies",
        ],
        "required": ["type", "project_id", "private_key", "private_key_id", "client_email", "token_uri"],
        "secret": ["private_key"],
    }

    @property
    def sqlalchemy_url(self):
        return URL(self.driver, self.project_id)

    def build_credentials(self, used_in_write_file: bool = False) -> dict:
        converted_key = self._convert_private_key(self.private_key, used_in_write_file=used_in_write_file)

        # Validate the converted private key if not used for write file
        if not used_in_write_file and not self.validate_private_key(converted_key):
            import logging

            logger = logging.getLogger(__name__)
            logger.error("Private key validation failed after conversion")
            logger.error(f"Original key preview: {self.private_key[:100] if self.private_key else 'None'}...")
            logger.error(f"Converted key preview: {converted_key[:100] if converted_key else 'None'}...")
            raise ValueError("Private key format is invalid after conversion. Please check the private key format.")

        return {
            "type": self.type,
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": converted_key,
            "client_email": self.client_email,
            "token_uri": self.token_uri,
        }

    def build_credentials_base64(self, used_in_write_file: bool = False) -> str:
        try:
            credentials_info = self.build_credentials(used_in_write_file=used_in_write_file)
            return base64.b64encode(json.dumps(credentials_info).encode("utf-8")).decode("utf-8")
        except Exception as e:
            # Log the error with context for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to build credentials: {str(e)}")
            logger.error(
                f"Private key preview (first 50 chars): {self.private_key[:50] if self.private_key else 'None'}..."
            )
            raise

    @staticmethod
    def _convert_private_key(private_key: str, used_in_write_file: bool = False) -> str:
        """
        Convert private key from various escape formats to proper PEM format.
        Handles multiple levels of escaping that can occur during transmission/storage.
        """
        if not private_key:
            return private_key

        # Remove any leading/trailing whitespace
        private_key = private_key.strip()

        # If used in write file, return as-is to preserve formatting
        if used_in_write_file:
            return private_key

        # Handle various escape sequence patterns
        # Multiple replacement passes to handle nested escaping

        # Replace quadruple-escaped newlines (\\\\n -> \\n)
        private_key = private_key.replace("\\\\n", "\\n")

        # Replace double-escaped newlines (\\n -> \n)
        private_key = private_key.replace("\\n", "\n")

        # Handle edge case where literal \n strings need to become actual newlines
        # This covers cases where the key was stored as a literal string
        if "-----BEGIN PRIVATE KEY-----" in private_key and "\n" not in private_key:
            # If we have the BEGIN marker but no actual newlines, it's likely escaped
            private_key = private_key.replace("-----BEGIN PRIVATE KEY-----", "-----BEGIN PRIVATE KEY-----\n")
            private_key = private_key.replace("-----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----")

            # Split the key content and add newlines every 64 characters (standard PEM format)
            lines = private_key.split("\n")
            if len(lines) >= 2:
                # Extract the key content between BEGIN and END
                begin_line = lines[0]
                end_line = lines[-1]
                key_content = "".join(lines[1:-1])

                # Split key content into 64-character lines
                formatted_lines = [begin_line]
                for i in range(0, len(key_content), 64):
                    formatted_lines.append(key_content[i : i + 64])
                formatted_lines.append(end_line)

                private_key = "\n".join(formatted_lines)

        return private_key

    def validate_private_key(self, private_key: str) -> bool:
        """
        Validate that the private key is in correct PEM format.
        Returns True if valid, False otherwise.
        """
        try:
            if not private_key:
                return False

            # Check for basic PEM structure
            if "-----BEGIN PRIVATE KEY-----" not in private_key:
                return False

            if "-----END PRIVATE KEY-----" not in private_key:
                return False

            # Check if we have proper newlines
            if "\n" not in private_key:
                return False

            # Try to parse with cryptography library (same as Google uses)
            from cryptography.hazmat.primitives import serialization

            try:
                serialization.load_pem_private_key(
                    private_key.encode("utf-8"),
                    password=None,
                )
                return True
            except Exception:
                return False

        except Exception:
            return False

    def init_proxy(self):
        if hasattr(self, "_proxy_inited"):
            return
        self._proxy_inited = True
        if not self.proxies:
            return

        for scheme in ["http", "https"]:
            os.environ[f"{scheme}_proxy"] = self.proxies[scheme]
        # todo: grpc proxy

    def connect(self):
        self.init_proxy()

        # Build URL with credentials_base64 and list_tables_page_size as query parameters
        from urllib.parse import quote_plus

        base_url = f"bigquery://{self.project_id}"

        # Prepare query parameters for BigQuery-specific settings
        credentials_b64 = self.build_credentials_base64()
        query_params = {"credentials_base64": quote_plus(credentials_b64), "list_tables_page_size": "100"}

        # Build the connection URL with query parameters
        query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
        connection_url = f"{base_url}?{query_string}"

        engine = create_engine(
            connection_url,
            arraysize=1000,
            max_overflow=0,  # todo: add to const
            pool_recycle=10 * 60,  # todo: add to const
            echo=True,  # todo
        )
        return engine  # todo: thread safe? use session to wrap?

    @with_ssh_tunnel
    def fetchall(self, query):
        """
        overwrite fetchall method to escape cursor's context manager,
        cuz google.cloud.bigquery.dbapi.cursor does not support context manager.
        """
        engine = self.connect()
        connection = engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @classmethod
    def get_sql_operator_types(cls):
        # pigeon type
        return [cls.connection_type, "google_bigquery"]

    @with_ssh_tunnel
    def get_tables(self, database: str = None) -> list[str]:
        def _format_table(table_name: str) -> str:
            # inspector will return jaffle_shop.table_name format
            return table_name.split(".")[-1]

        tables: list[str] = super().get_tables(database)
        return [_format_table(table_name) for table_name in tables]

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict:
        return {
            "method": "service-account-json",
            "project": self.project_id,
            "dataset": database or "stripe",  # todo: tmp
            "type": self.connection_type,
            "threads": 10,
            "keyfile_json": self.build_credentials(used_in_write_file=True),
            "timeout_seconds": 60,
            "priority": "interactive",
            "retries": 1,
        }

    def set_env_when_get_dbt_connection(self):
        pass

    @with_ssh_tunnel
    def get_columns(self, table: str, database: str = None) -> list:
        database = database or self.database
        query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM
            `{self.project_id}.{database}.INFORMATION_SCHEMA.COLUMNS`
        WHERE
            table_name = '{table}'
        """
        result = self.fetchall(query)
        column_metas = []
        for row in result:
            column_metas.append(
                {
                    "name": row[0],
                    "type": row[1].lower() if row[1] else None,
                    "nullable": row[2] == "YES",
                    "default": row[3],
                    "comment": "",
                }
            )
        return column_metas

    @cached_property
    @with_ssh_tunnel
    def type_code_mapping(self) -> dict:
        """
        type_code from sqlalchemy's cursor.description -> database's dialect data type name
        """
        return {x.upper(): x for x in self.available_column_types}

    def sqlalchemy_column_type_code_to_name(self, type_code: Any, size: int | None = None) -> str:
        # values refer to https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types
        # values of this mapping must be in available_column_types, or just default as string
        return type_code.lower()

    def convert_config_to_cube_config(self, database: str, schema: str = None, ds: DataSourceWrapper = None) -> dict:
        return {
            "type": "bigquery",
            "projectId": self.project_id,
            "credentials": self.build_credentials_base64(used_in_write_file=True),
        }
