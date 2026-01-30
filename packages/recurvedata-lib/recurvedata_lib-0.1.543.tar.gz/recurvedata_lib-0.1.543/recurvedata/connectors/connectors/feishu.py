try:
    from larksuiteoapi import DOMAIN_FEISHU, LEVEL_DEBUG, Config
    from larksuiteoapi.service.bot.v3.api import Service as BotV3Service
except ImportError:
    pass

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "feishu_bot"
UI_CONNECTION_TYPE = "Feishu"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class FeiShuBot(RecurveConnectorBase):
    setup_extras_require = ["larksuite-oapi"]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.INTEGRATION]

    config_schema = {
        "type": "object",
        "properties": {
            "app_id": {"type": "string", "title": _l("Feishu Bot App ID")},
            "app_secret": {"type": "string", "title": _l("Feishu Bot App Secret")},
        },
        "order": [
            "app_id",
            "app_secret",
        ],
        "required": [
            "app_id",
            "app_secret",
        ],
        "secret": [
            "app_secret",
        ],
    }

    @property
    def app_id(self):
        return self.conf["app_id"]

    @property
    def app_secret(self):
        return self.conf["app_secret"]

    @property
    def feishu_conf(self):
        if hasattr(self, "_feishu_conf"):
            return self._feishu_conf
        self.init_config()
        return self._feishu_conf

    def init_config(self):
        app_settings = Config.new_internal_app_settings(app_id=self.app_id, app_secret=self.app_secret)
        self._feishu_conf = Config(DOMAIN_FEISHU, app_settings, log_level=LEVEL_DEBUG)

    def test_connection(self):
        service = BotV3Service(self.feishu_conf)
        resp = service.bots.get().do()
        if resp.code != 0:
            raise ValueError(f"{resp.msg} {resp.error}")
