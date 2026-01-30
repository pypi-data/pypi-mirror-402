from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.utils.imports import MockModule

try:
    import jenkins
except ImportError:
    jenkins = MockModule("jenkins")

CONNECTION_TYPE = "jenkins"
UI_CONNECTION_TYPE = "Jenkins"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class Jenkins(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = [
        "python-jenkins",
    ]

    config_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "title": "url"},
            "user": {"type": "string", "title": "Username"},
            "password": {"type": "string", "title": "Password"},
        },
        "order": [
            "url",
            "user",
            "password",
        ],
        "required": [
            "url",
            "user",
            "password",
        ],
        "secret": ["password"],
    }

    def __init__(self, conf: dict, *args, **kwargs):
        super().__init__(conf, *args, **kwargs)
        self.conf = conf
        self.connector = self.init_connection(conf)

    def init_connection(self, conf):
        return jenkins.Jenkins(url=conf["url"], username=conf["user"], password=conf["password"])

    def test_connection(self):
        self.connector.get_whoami()
