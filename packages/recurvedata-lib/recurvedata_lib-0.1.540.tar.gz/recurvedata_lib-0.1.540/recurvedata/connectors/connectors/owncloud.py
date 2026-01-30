from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "owncloud"
UI_CONNECTION_TYPE = "OwnCloud"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class OwnCloud(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    category = [ConnectionCategory.STORAGE]
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "title": _l("Host URL")},
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "dav_endpoint_version": {
                "type": "number",
                "title": _l("WebDAV Endpoint Version"),
                "default": 1,
            },
        },
        "order": ["url", "user", "password", "dav_endpoint_version"],
        "required": ["url", "user", "password"],
        "secret": ["password"],
    }

    def test_connection(self):
        # todo: 暂不校验
        pass
