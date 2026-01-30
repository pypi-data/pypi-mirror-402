import base64

import requests

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

# https://api.guandata.com/apidoc/docs-site/345092

CONNECTION_TYPE = "guanyuan_bi"
UI_CONNECTION_TYPE = "Guanyuan BI"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class GuanyuanBI(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    category = [ConnectionCategory.BI]

    config_schema = {
        "type": "object",
        "properties": {
            "base_url": {"type": "string", "title": _l("Base URL")},
            "app_token": {"type": "string", "title": _l("App Token")},
            "domain": {"type": "string", "title": _l("Domain")},
            "login_id": {"type": "string", "title": _l("Login ID")},
            "password": {"type": "string", "title": _l("Password")},
            "version": {
                "type": "string",
                "title": _l("Version"),
                "default": "8.1.0",
            },
        },
        "order": ["base_url", "app_token", "domain", "login_id", "password", "version"],
        "required": ["base_url", "app_token", "domain", "login_id", "password"],
        "secret": ["password"],
    }

    def test_connection(self):
        encoded_password = base64.b64encode(self.password.encode() if self.password else b"").decode()
        payload = {
            "domain": self.domain,
            "loginId": self.login_id,
            "password": encoded_password,
        }
        resp = requests.post(f"{self.base_url}/public-api/sign-in", json=payload)
        resp.raise_for_status()
        json_result = resp.json()
        user_token = json_result.get("response", {}).get("token")
        assert user_token is not None, f"sign in failed, response: {json_result}"
        return user_token
