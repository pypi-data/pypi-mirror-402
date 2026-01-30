from sqlalchemy.engine import URL

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.dbapi import DBAPIBase
from recurvedata.consts import ConnectorGroup

CONNECTION_TYPE = "phoenix"
UI_CONNECTION_TYPE = "HBase Phoenix"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class PhoenixConnector(DBAPIBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    setup_extras_require = ["sqlalchemy-phoenix"]
    driver = "phoenix"

    config_schema = {
        "type": "object",
        "properties": {
            "host": {"type": "string", "title": "Host Address"},
            "port": {
                "type": "number",
                "title": "Port Number",
                "default": 8765,
            },
        },
        "order": ["host", "port"],
        "required": ["host", "port"],
        "secret": [],
    }

    @property
    def sqlalchemy_url(self):
        return URL(self.driver, host=self.host, port=self.port)
