from collections import OrderedDict
from typing import Any, Optional

import pyodbc

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.mssql import BaseAzureSQLConnector
from recurvedata.pigeon.schema import types
from recurvedata.pigeon.utils import safe_int


@register_connector_class("microsoft_fabric")  # type: ignore
class MsFabricConnector(BaseAzureSQLConnector):
    """Connector for Microsoft Fabric.

    This connector extends BaseAzureSQLConnector to support Microsoft Fabric specific features:
    - Azure AD authentication
    - Workspace-level access control
    - Special ODBC driver configuration
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        schema: str | None = None,
        tenant_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        authentication: str = "ServicePrincipal",
        odbc_driver: str = "ODBC Driver 18 for SQL Server",
        encrypt: bool = True,
        trust_server_certificate: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(host, port, database, schema=schema, *args, **kwargs)
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authentication = authentication
        self.odbc_driver = odbc_driver
        self.driver = "mssql+pyodbc"
        self.encrypt = encrypt
        self.trust_server_certificate = trust_server_certificate

    def _get_sqlalchemy_uri(self) -> str:
        """Generate SQLAlchemy URI for Microsoft Fabric."""
        return (
            f"{self.driver}://{self.client_id}:{self.client_secret}@{self.host}:{self.port}/"
            f"{self.database}?driver={self.odbc_driver}&encrypt={self.encrypt}&trust_server_certificate={self.trust_server_certificate}"
        )

    def is_fabric(self) -> bool:
        """Check if this is a Microsoft Fabric connector."""
        return True

    @staticmethod
    def to_canonical_type(type_code: Any, size: Optional[int] = None) -> str:
        """Convert Microsoft Fabric type to canonical type."""
        return BaseAzureSQLConnector.to_canonical_type(type_code, size)

    @staticmethod
    def from_canonical_type(canonical_type: str, size: Optional[int] = None) -> str:
        """Convert canonical type to Microsoft Fabric type."""
        if canonical_type == types.STRING:
            if size is None or size == 0:
                return "VARCHAR(max)"
            safe_size = safe_int(size * 4)
            if safe_size > 4000:
                return "VARCHAR(max)"
            return f"VARCHAR({safe_size})"
        return BaseAzureSQLConnector.from_canonical_type(canonical_type, size)

    @property
    def conn_string(self) -> str:
        """Generate connection string for Microsoft Fabric with Azure AD authentication."""
        options = OrderedDict(
            {
                "Driver": f"{{{self.odbc_driver}}}",
                "Server": f"{self.host}",
                "Database": str(self.database),
                "Authentication": "ActiveDirectoryServicePrincipal",
                "Encrypt": "yes" if self.encrypt else "no",
                "TrustServerCertificate": "yes" if self.trust_server_certificate else "no",
                "Uid": self.client_id,
                "Pwd": self.client_secret,
                "Connection Timeout": 30,
            }
        )
        return ";".join([f"{k}={v}" for k, v in options.items()])

    def connect_impl(self, autocommit=False, *args, **kwargs):
        return pyodbc.connect(self.conn_string, autocommit=autocommit)
