try:
    from adlfs import AzureBlobFileSystem
except ImportError:
    AzureBlobFileSystem = None

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.object_store import ObjectStoreMixin
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "azure_blob"
UI_CONNECTION_TYPE = "Azure Blob Storage"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class AzureBlob(ObjectStoreMixin):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = [
        "fsspec[adl]",
    ]
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "connection_string": {
                "type": "string",
                "title": _l("Connection String"),
                "description": _l("Azure Storage connection string containing authentication details"),
            },
            "account_name": {"type": "string", "title": _l("Storage Account Name")},
            "account_key": {"type": "string", "title": _l("Account Access Key")},
            "sas_token": {"type": "string", "title": _l("SAS Token")},
            "container": {"type": "string", "title": _l("Container Name")},
            "endpoint_suffix": {
                "type": "string",
                "title": _l("Endpoint Suffix"),
                "description": _l("Storage endpoint suffix (e.g. core.windows.net)"),
            },
        },
        "order": ["connection_string", "account_name", "account_key", "sas_token", "container", "endpoint_suffix"],
        "required": [],
        "secret": ["account_key", "sas_token"],
    }

    def init_connection(self, conf) -> AzureBlobFileSystem:
        con = AzureBlobFileSystem(
            connection_string=self.connection_string,
            account_name=conf.get("account_name"),
            account_key=conf.get("account_key"),
            sas_token=conf.get("sas_token"),
            container_name=conf.get("container"),
        )
        self.connector = con
        return con

    @property
    def connection_string(self):
        if self.conf.get("connection_string"):
            return self.conf["connection_string"]
        parts = [
            "DefaultEndpointsProtocol=https",
        ]
        if self.account_name:
            parts.append(f"AccountName={self.account_name}")
        if self.endpoint_suffix:
            parts.append(f"EndpointSuffix={self.endpoint_suffix}")
        if self.sas_token:
            parts.append(f"SharedAccessSignature={self.sas_token}")
        return ";".join(parts)

    @property
    def bucket(self):
        return self.conf.get("container")

    def test_connection(self):
        try:
            self.connector.exists(self.bucket_key(""))
        except Exception as e:
            if "This request is not authorized to perform this operation" in str(e):
                self.connector.ls(self.bucket_key(""))  # todo: return_glob?
                return
            raise

    juice_sync_able = True

    def juice_sync_path(self, path: str) -> str:
        return f"wasb://{path}"  # todo
