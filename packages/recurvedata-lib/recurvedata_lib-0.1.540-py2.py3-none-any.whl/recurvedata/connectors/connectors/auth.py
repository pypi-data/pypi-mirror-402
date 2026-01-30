import json

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.core.translation import _l

CONNECTION_TYPE = "auth"
UI_CONNECTION_TYPE = "Auth"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class Auth(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE

    config_schema = {
        "type": "object",
        "properties": {
            "host": {"type": "string", "title": _l("Host Address")},
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "port": {"type": "number", "title": _l("Port Number")},
            "extra": {
                "type": "string",
                "title": _l("Additional Configuration"),
                "description": _l("Additional configuration parameters in JSON format"),
                "ui:options": {"type": "textarea"},
            },
        },
        "order": ["host", "user", "password", "port", "extra"],
        "required": ["host"],
        "secret": ["password"],
    }

    def test_connection(self):
        pass

    @staticmethod
    def preprocess_conf(data):
        data = RecurveConnectorBase.preprocess_conf(data)
        json_data = data.get("extra")
        if json_data and isinstance(json_data, str):
            data["extra"] = json.loads(json_data)
        return data
