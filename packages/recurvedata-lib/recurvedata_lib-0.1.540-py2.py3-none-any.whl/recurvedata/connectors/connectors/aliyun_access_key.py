from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "aliyun_access_key"
UI_CONNECTION_TYPE = "Aliyun Access Key"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class AliyunAccessKeyConnector(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    test_required = False

    config_schema = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string", "title": _l("Endpoint")},
            "access_key_id": {"type": "string", "title": _l("Access Key ID")},
            "access_key_secret": {"type": "string", "title": _l("Access Key Secret")},
        },
        "order": ["endpoint", "access_key_id", "access_key_secret"],
        "required": ["endpoint", "access_key_id", "access_key_secret"],
        "secret": ["access_key_secret"],
    }

    def test_connection(self):
        pass
