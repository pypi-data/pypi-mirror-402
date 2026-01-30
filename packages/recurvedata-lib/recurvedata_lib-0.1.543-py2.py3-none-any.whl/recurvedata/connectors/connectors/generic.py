import json

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "generic"
UI_CONNECTION_TYPE = "Generic"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class GenericConnector(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    test_required = False

    config_schema = {
        "type": "object",
        "properties": {
            "host": {"type": "string", "title": _l("Host")},
            "port": {"type": "integer", "title": _l("Port")},
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "timeout": {"type": "integer", "title": _l("Timeout (seconds)"), "default": 30},
            "custom": {
                "type": "string",
                "title": _l("Custom Configuration"),
                "description": _l("Custom configuration parameters in JSON format"),
                "ui:field": "CodeEditorWithReferencesField",
                "ui:options": {"type": "code", "lang": "json"},
            },
        },
        "order": ["host", "port", "user", "password", "timeout", "custom"],
        "required": ["host", "port", "user", "password"],
        "secret": ["password"],
    }

    def test_connection(self):
        pass

    @staticmethod
    def preprocess_conf(data):
        data = RecurveConnectorBase.preprocess_conf(data)
        json_data = data.get("custom")
        if json_data and isinstance(json_data, str):
            data["custom"] = json.loads(json_data)
        return data
