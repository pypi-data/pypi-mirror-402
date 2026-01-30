from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "slack"
UI_CONNECTION_TYPE = "Slack"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class FeiShuBot(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.INTEGRATION]

    config_schema = {
        "type": "object",
        "properties": {
            "app_token": {
                "type": "string",
                "title": _l("Slack App Token"),
                "description": _l("The token used to authenticate with Slack API"),
            },
        },
        "required": [
            "app_token",
        ],
        "secret": [
            "app_token",
        ],
    }

    @property
    def app_token(self):
        return self.conf["app_token"]
