from sqlalchemy.engine import URL

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.dbapi import DBAPIBase
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "azure_synapse"
UI_CONNECTION_TYPE = "Azure Synapse"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class SynapseConnector(DBAPIBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = ["pyodbc"]
    driver = "mssql+pyodbc"

    category = [
        ConnectionCategory.WAREHOUSE,
    ]
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "host": {"type": "string", "title": _l("Host Address")},
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 1433,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {"type": "string", "title": _l("Database Name")},
            "odbc_driver": {
                "type": "string",
                "title": _l("ODBC Driver"),
                "default": "ODBC Driver 17 for SQL Server",
            },
            "blob_options": {
                "type": "object",
                "title": _l("Azure Blob Storage Options"),
                "properties": {
                    "account_name": {"type": "string", "title": _l("Storage Account Name")},
                    "sas_token": {"type": "string", "title": _l("SAS Token")},
                },
                "order": ["account_name", "sas_token"],
            },
        },
        "order": ["host", "port", "user", "password", "database", "odbc_driver", "blob_options"],
        "required": ["host", "port"],
        "secret": ["password", "blob_options.sas_token"],
    }

    # todo: autocommit

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
            query={"driver": self.odbc_driver, "autocommit": "True"},
        )

    def connect(self):
        engine = super().connect()
        # engine = engine.execution_options(
        #     isolation_level="AUTOCOMMIT"
        # )
        return engine
