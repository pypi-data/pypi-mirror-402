try:
    from fsspec.implementations.ftp import FTPFileSystem
except ImportError:
    FTPFileSystem = None

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.ftp import FTPMixin
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "ftp"
UI_CONNECTION_TYPE = "FTP"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class FTP(FTPMixin):
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
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 21,
            },
        },
        "order": [
            "host",
            "port",
            "user",
            "password",
        ],
        "required": ["host", "port"],
        "secret": ["password"],
    }

    def init_connection(self, conf) -> FTPFileSystem:
        con = FTPFileSystem(host=conf["host"], port=conf["port"], user=conf["user"], password=conf["password"])
        self.connector = con
        return con
