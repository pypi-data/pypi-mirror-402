from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.object_store import ObjectStoreMixin
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "cos"
UI_CONNECTION_TYPE = "Tencent COS"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class COS(ObjectStoreMixin):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    setup_extras_require = []

    config_schema = {
        "type": "object",
        "properties": {
            "secret_id": {"type": "string", "title": _l("Tencent Cloud API Secret ID")},
            "secret_key": {"type": "string", "title": _l("Tencent Cloud API Secret Key")},
            "region": {"type": "string", "title": _l("COS Region"), "default": "ap-guangzhou"},
            "bucket": {"type": "string", "title": _l("Bucket Name")},
        },
        "order": ["secret_id", "secret_key", "region", "bucket"],
        "required": ["secret_id", "secret_key", "region", "bucket"],
        "secret": ["secret_key"],
    }

    def init_connection(self, conf):
        self.connector = None  # todo

    def test_connection(self):
        # todo
        pass

    juice_sync_able = True

    def juice_sync_path(self, path: str) -> str:
        return f"cos://{path}"  # todo
