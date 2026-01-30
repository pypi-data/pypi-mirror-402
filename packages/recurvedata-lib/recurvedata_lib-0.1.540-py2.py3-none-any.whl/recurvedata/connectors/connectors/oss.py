try:
    from ossfs import OSSFileSystem
except ImportError:
    OSSFileSystem = None

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.object_store import ObjectStoreMixin
from recurvedata.connectors.proxy import HTTP_PROXY_CONFIG_SCHEMA, HttpProxyMixin
from recurvedata.connectors.utils import juice_sync_process_special_character_within_secret
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "oss"
UI_CONNECTION_TYPE = "Aliyun OSS"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class OSS(HttpProxyMixin, ObjectStoreMixin):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    setup_extras_require = ["ossfs"]

    config_schema = {
        "type": "object",
        "properties": {
            "access_key_id": {
                "type": "string",
                "title": _l("Aliyun Access Key ID"),
                "description": _l("The AccessKey ID for authenticating with Aliyun OSS"),
            },
            "secret_access_key": {
                "type": "string",
                "title": _l("Aliyun Secret Access Key"),
                "description": _l("The AccessKey Secret for authenticating with Aliyun OSS"),
            },
            "endpoint": {
                "type": "string",
                "title": _l("OSS Endpoint"),
                "description": _l("The endpoint URL for your OSS bucket region"),
                "default": "oss-cn-hangzhou.aliyuncs.com",
            },
            "bucket": {"type": "string", "title": _l("Bucket Name")},
            "proxies": HTTP_PROXY_CONFIG_SCHEMA["proxies"],
        },
        "order": [
            "access_key_id",
            "secret_access_key",
            "endpoint",
            "bucket",
            "proxies",
        ],
        "required": ["access_key_id", "secret_access_key", "endpoint", "bucket"],
        "secret": ["secret_access_key"],
    }

    def init_connection(self, conf) -> OSSFileSystem:
        con = OSSFileSystem(
            key=conf["access_key_id"],
            secret=conf["secret_access_key"],
            endpoint=conf["endpoint"],
        )
        self.connector = con
        return con

    juice_sync_able = True

    def juice_sync_path(self, path: str) -> tuple[str, str]:
        secret_part = f"{self.access_key_id}:{self.secret_access_key}"
        secret_part = juice_sync_process_special_character_within_secret(secret_part)
        common_part = f'{self.bucket}.{self.endpoint}/{path.lstrip("/")}'
        secret_path = f"oss://{secret_part}@{common_part}"
        non_secret_path = f"oss://{common_part}"
        return secret_path, non_secret_path
