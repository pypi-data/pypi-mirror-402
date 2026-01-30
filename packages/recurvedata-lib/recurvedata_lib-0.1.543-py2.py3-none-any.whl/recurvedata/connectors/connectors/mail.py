from smtplib import SMTP, SMTP_SSL

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.core.translation import _l

CONNECTION_TYPE = "mail"
UI_CONNECTION_TYPE = "Mail"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class Mail(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE

    config_schema = {
        "type": "object",
        "properties": {
            "host": {"type": "string", "title": _l("SMTP Server Address")},
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 465,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "reply_to": {
                "type": "string",
                "title": _l("Reply-To Address"),
                "description": _l("Email address that recipients will reply to"),
            },
            "mail_from": {
                "type": "string",
                "title": _l("From Address"),
                "description": _l("Email address that appears in the From field"),
            },
            "ssl": {
                "type": "boolean",
                "title": _l("Use SSL/TLS"),
                "description": _l("Enable SSL/TLS encryption for secure email transmission"),
                "default": True,
            },
            "timeout": {
                "type": "number",
                "title": _l("Connection Timeout"),
                "description": _l("Maximum time in seconds to wait for server connection"),
                "default": 180,
            },
        },
        "order": [
            "host",
            "port",
            "user",
            "password",
            "reply_to",
            "mail_from",
            "ssl",
            "timeout",
        ],
        "required": ["host", "port", "user", "password"],
        "secret": ["password"],
    }

    def __init__(self, conf: dict, *args, **kwargs):
        self.conf = conf
        self.connector, self.connector_err = self.init_connection(conf)

    def init_connection(self, conf: dict):
        try:
            smtp_class = SMTP if not conf.get("ssl") else SMTP_SSL
            smtp = smtp_class(host=conf["host"], port=conf["port"], timeout=conf.get("timeout", 180))
            if conf.get("user") and conf.get("password"):
                smtp.login(conf["user"], conf["password"])
            return smtp, None
        except Exception as e:
            return None, e

    def test_connection(self):
        if self.connector_err:
            raise ValueError(f"Failed to connect: {self.connector_err}")
        if not self.connector:
            raise ValueError("SMTP connection not initialized")

        try:
            res = self.connector.noop()
            if res[0] != 250:
                raise ValueError(f"SMTP server returned unexpected response: {res}")
        except Exception as e:
            raise ValueError(f"SMTP connection test failed: {str(e)}")
