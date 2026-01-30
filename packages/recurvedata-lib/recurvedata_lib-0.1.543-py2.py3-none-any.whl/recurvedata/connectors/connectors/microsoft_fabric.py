import datetime
import logging
import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy.engine import URL

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.connectors.mssql import MssqlConnector
from recurvedata.consts import ConnectionCategory
from recurvedata.core.translation import _l

CONNECTION_TYPE = "microsoft_fabric"
UI_CONNECTION_TYPE = "Microsoft Fabric"


class AuthMethod(StrEnum):
    """Microsoft Fabric authentication methods"""

    SERVICE_PRINCIPAL = "ActiveDirectoryServicePrincipal"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class MsFabricConnector(MssqlConnector):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    category = [ConnectionCategory.WAREHOUSE]
    SYSTEM_DATABASES = [
        "information_schema",
        "sys",
        "db_owner",
        "db_datareader",
        "db_datawriter",
        "db_ddladmin",
        "db_securityadmin",
        "db_accessadmin",
        "db_backupoperator",
        "db_denydatawriter",
        "db_denydatareader",
        "_rsc",
        "queryinsights",
        "guest",
    ]

    available_column_types = [
        "bit",
        "smallint",
        "int",
        "bigint",
        "decimal",
        "numeric",
        "float",
        "real",
        "date",
        "time",
        "datetime2",
        "char",
        "varchar",
        "varbinary",
        "uniqueidentifier",
    ]

    column_type_mapping = {
        "integer": ["smallint", "int", "bigint"],
        "float": ["real", "float"],
        "datetime": ["datetime2"],
        "string": ["char", "varchar"],
        "binary": ["varbinary", "uniqueidentifier"],
    }

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
                "default": 1433,
            },
            "authentication": {
                "type": "string",
                "title": _l("Authentication Method"),
                "default": "ActiveDirectoryServicePrincipal",
                "ui:options": {
                    "disabled": True,
                },
            },
            "tenant_id": {
                "type": "string",
                "title": _l("Tenant ID"),
            },
            "client_id": {
                "type": "string",
                "title": _l("Client ID"),
            },
            "client_secret": {
                "type": "string",
                "title": _l("Client Secret"),
            },
            "database": {
                "type": "string",
                "title": _l("Database Name"),
            },
            "odbc_driver": {
                "type": "string",
                "title": _l("ODBC Driver"),
                "default": "ODBC Driver 18 for SQL Server",
                "ui:options": {
                    "disabled": True,
                },
            },
            "encrypt": {
                "type": "boolean",
                "title": _l("Encrypt Connection"),
                "description": _l("Whether to encrypt the connection"),
                "default": True,
            },
            "trust_server_certificate": {
                "type": "boolean",
                "title": _l("Trust Server Certificate"),
                "default": True,
            },
            "blob_options": {
                "type": "object",
                "title": _l("Azure Blob Storage Options"),
                "properties": {
                    "account_name": {"type": "string", "title": _l("Storage Account Name")},
                    "endpoint_suffix": {"type": "string", "title": _l("Endpoint Suffix")},
                    "container_name": {"type": "string", "title": _l("Container Name")},
                    "sas_token": {"type": "string", "title": _l("SAS Token")},
                },
                "order": ["account_name", "endpoint_suffix", "container_name", "sas_token"],
            },
        },
        "order": [
            "host",
            "port",
            "authentication",
            "tenant_id",
            "client_id",
            "client_secret",
            "database",
            "odbc_driver",
            "encrypt",
            "trust_server_certificate",
            "blob_options",
        ],
        "required": ["host", "port", "tenant_id", "client_id", "client_secret", "database"],
        "secret": ["client_secret", "blob_options.sas_token"],
    }

    INT_TYPE_MAPPING = {
        range(0, 4): "tinyint",
        range(4, 6): "smallint",
        range(6, 11): "int",
        range(11, 20): "bigint",
    }

    BASE_TYPE_MAPPING = {
        bool: "bit",
        float: "float",
        datetime.datetime: "datetime2",
        str: "varchar",
        bytes: "varbinary",
        uuid.UUID: "uniqueidentifier",
    }

    @property
    def sqlalchemy_url(self):
        query = {
            "driver": self.odbc_driver,
            "authentication": AuthMethod.SERVICE_PRINCIPAL.value,
            "Encrypt": "yes" if self.conf.get("encrypt", True) else "no",
            "TrustServerCertificate": "yes" if self.conf.get("trust_server_certificate", True) else "no",
            "Tenant Id": self.conf["tenant_id"],
        }

        url = URL(
            self.driver,
            self.conf["client_id"],
            self.conf["client_secret"],
            self.conf["host"],
            self.conf["port"],
            self.conf["database"],
            query=query,
        )

        # Debug logging
        logging.info(f"Connection URL (without credentials): {url.render_as_string(hide_password=True)}")
        return url

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict[str, Any]:
        return {
            "server": self.conf["host"],
            "port": self.conf["port"],
            "client_id": self.conf["client_id"],
            "client_secret": self.conf["client_secret"],
            "database": database or self.database,
            "type": "fabric",
            "authentication": "ServicePrincipal",
            "tenant_id": self.conf["tenant_id"],
            "schema": schema or database or self.database,
            "driver": self.odbc_driver,
        }

    def sqlalchemy_column_type_code_to_name(self, type_code: Any, size: int | None = None) -> str:
        """
        Map SQL Server/Microsoft Fabric type codes to their corresponding type names.
        Reference: https://learn.microsoft.com/en-us/fabric/data-warehouse/data-types

        Microsoft Fabric supports a subset of T-SQL data types, including:
        - Exact numerics: bit, smallint, int, bigint, decimal/numeric
        - Approximate numerics: float, real
        - Date and time: date, time, datetime2
        - Character strings: char, varchar
        - Binary strings: varbinary, uniqueidentifier
        """
        # First try to get the Python type from type_code
        py_type = type(type_code) if type_code is not None else None

        # If type_code itself is a type (like int, str, etc), use it directly
        if isinstance(type_code, type):
            py_type = type_code

        type_mapping = {
            bool: "bit",
            int: "int",
            float: "float",
            datetime.datetime: "datetime2",
            str: "varchar",
            bytes: "varbinary",
            uuid.UUID: "uniqueidentifier",
        }

        if py_type in type_mapping:
            base_type = type_mapping[py_type]
            if py_type is int and size is not None:
                for size_range, type_name in self.INT_TYPE_MAPPING.items():
                    if size in size_range:
                        return type_name
            return base_type

        return "varchar"

    def set_env_when_get_dbt_connection(self):
        pass

    @classmethod
    def limit_sql(
        cls, sql: str, limit: int = 100, orders: list[dict[str, str]] | None = None, offset: int | None = None
    ) -> str:
        """Add pagination to SQL query for Microsoft Fabric.

        Args:
            sql: The SQL query to add limit to
            limit: Maximum number of rows to return
            orders: List of order by clauses
            offset: Number of rows to skip

        Returns:
            SQL query with pagination
        """
        # dbt model with `ephemeral` will automatically add `__dbt__cte__` to the query
        # which is not supported by Microsoft Fabric
        # so we need to handle it separately
        if "__dbt__cte__" not in sql and not sql.upper().strip().startswith("WITH"):
            return super().limit_sql(sql, limit, orders, offset)

        sql = cls.order_sql(sql, orders)

        # Build final query with CTE
        sub_query_name = "_recurve_limit_subquery"
        base_sql = f"WITH {sub_query_name} AS ({sql})"

        if offset:
            base_sql = f"{base_sql} ORDER BY (SELECT NULL)"
            return f"{base_sql} SELECT * FROM {sub_query_name} OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"

        return f"{base_sql} SELECT TOP {limit} * FROM {sub_query_name}"
