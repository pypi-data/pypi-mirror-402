import os

from recurvedata.consts import ConnectorGroup

try:
    from fsspec.implementations.sftp import SFTPFileSystem
except ImportError:
    SFTPFileSystem = None

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.ftp import FTPMixin
from recurvedata.core.translation import _l

CONNECTION_TYPE = "sftp"
UI_CONNECTION_TYPE = "SFTP"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class SFTP(FTPMixin):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    setup_extras_require = ["fsspec[sftp]", "paramiko"]

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
                "default": 22,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "private_key_path": {"type": "string", "title": _l("Private Key File Path")},
        },
        "order": ["host", "port", "user", "password", "private_key_path"],
        "required": ["host", "port"],
        "secret": ["password"],
    }

    def _build_ssh_kwargs(self) -> dict:
        """
        build fsspec ssh_kwargs
        :return:
        """
        import paramiko

        pkey = None
        pk_path = self.conf.get("private_key_path")
        if pk_path:
            pk_path = os.path.expanduser(pk_path)
            pkey = paramiko.RSAKey.from_private_key_file(pk_path, password=self.conf.get("password"))
        return {
            "username": self.conf["user"],
            "password": self.conf.get("password"),
            "port": self.conf["port"],
            "pkey": pkey,
        }

    def init_connection(self, conf) -> SFTPFileSystem:
        con = SFTPFileSystem(host=conf["host"], **self._build_ssh_kwargs())
        self.connector = con
        return con

    def test_connection(self):
        self.connector.ls(".")

    juice_sync_able = True

    def juice_sync_path(self, path: str) -> str:
        from urllib.parse import quote

        username = self.conf["user"]
        password = self.conf["password"]
        password = quote(password)
        port = self.conf["port"]
        host = self.conf["host"]
        # tmp only allow password
        secret_path = f"{username}:{password}@{host}:{port}{path}"
        non_secret_path = f"{username}:********@{host}:{port}{path}"
        return secret_path, non_secret_path
