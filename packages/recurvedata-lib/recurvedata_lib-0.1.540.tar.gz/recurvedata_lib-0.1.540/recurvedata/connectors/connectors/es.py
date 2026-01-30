from sqlalchemy.engine import URL

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.dbapi import DBAPIBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "elasticsearch"
UI_CONNECTION_TYPE = "Elasticsearch"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class ElasticSearchConnector(DBAPIBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]

    setup_extras_require = ["elasticsearch-dbapi"]
    driver = "elasticsearch"
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
                "default": 9200,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
        },
        "order": [
            "host",
            "port",
            "user",
            "password",
        ],
        "required": [
            "host",
        ],
        "secret": ["password"],
    }

    @property
    def user(self):  # todo
        return self.conf.get("user")

    @property
    def password(self):  # todo
        return self.conf.get("password")

    @property
    def sqlalchemy_url(self):
        return URL(self.driver, self.user, self.password, self.host, self.port)

    @classmethod
    def get_sql_operator_types(cls):
        return []
