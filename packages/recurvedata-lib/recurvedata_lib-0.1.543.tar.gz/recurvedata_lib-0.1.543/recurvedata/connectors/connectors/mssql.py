from sqlalchemy.engine import URL

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.dbapi import DBAPIBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "mssql"
UI_CONNECTION_TYPE = "Microsoft SQL Server"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class MssqlConnector(DBAPIBase):
    SYSTEM_DATABASES = ["master", "model", "msdb", "tempdb"]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]

    setup_extras_require = ["pyodbc"]
    driver = "mssql+pyodbc"

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
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
                "default": "default",
            },
            "odbc_driver": {
                "type": "string",
                "title": _l("ODBC Driver"),
                "default": "ODBC Driver 18 for SQL Server",
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
        },
        "order": ["host", "port", "user", "password", "database", "odbc_driver", "encrypt", "trust_server_certificate"],
        "required": [
            "host",
        ],
        "secret": ["password"],
    }

    @property
    def odbc_driver(self):
        return self.conf["odbc_driver"]

    @property
    def sqlalchemy_url(self):
        return URL(
            self.driver,
            self.user,
            self.password,
            self.host,
            self.port,
            self.database,
            query={
                "driver": self.odbc_driver,
                "TrustServerCertificate": "yes" if self.conf.get("trust_server_certificate", False) else "no",
                "Encrypt": "yes" if self.conf.get("encrypt", True) else "no",
            },
        )

    @classmethod
    def get_sql_operator_types(cls):
        return [cls.connection_type, "azure_mssql"]

    @classmethod
    def order_sql(cls, sql: str, orders: list[dict[str, str]] | None = None, return_sql: bool = True) -> str:
        """Format SQL with ORDER BY clause for MSSQL.

        Args:
            sql: The SQL query to add ORDER BY to
            orders: List of dicts with column and order direction
            return_sql: Whether to return the formatted SQL

        Returns:
            SQL query with ORDER BY clause
        """
        if not orders:
            return sql

        order_clauses = [f"{order['field']} {order['order']}" for order in orders]
        order_by = f" ORDER BY {', '.join(order_clauses)}"
        return f"{sql}{order_by}"

    @classmethod
    def limit_sql(
        cls, sql: str, limit: int = 100, orders: list[dict[str, str]] | None = None, offset: int | None = None
    ) -> str:
        """Add TOP/OFFSET-FETCH clause to SQL query for MSSQL.

        Args:
            sql: The SQL query to add limit to
            limit: Maximum number of rows to return
            orders: List of order by clauses
            offset: Number of rows to skip

        Returns:
            SQL query with TOP/OFFSET-FETCH clause
        """
        sub_query_name = "_recurve_limit_subquery"
        sql = cls.order_sql(sql, orders)

        if offset:
            return f"{sql} OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"

        return f"SELECT TOP {limit} * FROM ({sql}) AS {sub_query_name}"
