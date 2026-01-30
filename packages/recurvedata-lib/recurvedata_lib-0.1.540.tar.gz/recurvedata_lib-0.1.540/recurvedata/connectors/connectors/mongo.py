try:
    from pymongo import MongoClient
except ImportError:
    pass

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "mongodb"
UI_CONNECTION_TYPE = "MongoDB"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class MongoDB(DBAPIBase):
    SYSTEM_DATABASES = [
        "admin",
        "config",
        "local",
    ]
    setup_extras_require = ["pymongo"]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]

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
                "default": 27017,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "authSource": {
                "type": "string",
                "title": _l("Authentication Database"),
                "default": "admin",
            },
            "directConnection": {
                "type": "boolean",
                "title": _l("Direct Connection"),
                "default": False,
                "description": _l("Whether to use direct connection to the MongoDB server"),
            },
        },
        "order": ["host", "port", "user", "password", "authSource", "directConnection"],
        "required": ["host", "port", "user", "password"],
        "secret": ["password"],
    }

    def test_connection(self):
        client = MongoClient(
            host=self.conf["host"],
            port=self.conf["port"],
            username=self.conf["user"],
            password=self.conf["password"],
            authSource=self.conf["authSource"],
            serverSelectionTimeoutMS=5000,
            directConnection=self.conf["directConnection"],
        )
        client.admin.command("ping")

    @classmethod
    def get_sql_operator_types(cls) -> list[str]:
        return []

    @with_ssh_tunnel
    def get_databases(self) -> list[str]:
        client = MongoClient(
            host=self.conf["host"],
            port=self.conf["port"],
            username=self.conf["user"],
            password=self.conf["password"],
            authSource=self.conf["authSource"],
            serverSelectionTimeoutMS=5000,
            directConnection=self.conf["directConnection"],
        )
        databases = client.list_database_names()
        return [d for d in databases if d not in self.SYSTEM_DATABASES]
