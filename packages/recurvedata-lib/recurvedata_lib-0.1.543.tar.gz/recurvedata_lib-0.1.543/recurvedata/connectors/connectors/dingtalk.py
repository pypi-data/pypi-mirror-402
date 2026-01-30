import requests

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "dingtalk"
UI_CONNECTION_TYPE = "Ding Talk"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class DingTalk(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.INTEGRATION]
    enabled = False

    config_schema = {
        "type": "object",
        "properties": {
            "app_key": {"type": "string", "title": _l("DingTalk App Key")},
            "app_secret": {"type": "string", "title": _l("DingTalk App Secret")},
            "phone": {
                "type": "string",
                "title": _l("Phone Number"),
                "description": _l("Phone number associated with the DingTalk account"),
            },
        },
        "order": ["app_key", "app_secret", "phone"],
        "required": ["app_key", "app_secret"],
        "secret": ["app_secret"],
    }

    def test_connection(self):
        access_token = self.get_token()
        if self.phone:
            self.get_user_id_by_phone(access_token)

    def get_token(self):
        """
        获取钉钉的访问令牌
        """
        url = f"https://oapi.dingtalk.com/gettoken?appkey={self.app_key}&appsecret={self.app_secret}"
        resp = requests.get(url)
        data = resp.json()
        if data.get("errcode"):
            raise ValueError(f"get_token fail, response data: {data}")
        return data["access_token"]

    def get_user_id_by_phone(self, access_token):
        """
        获取 user id
        """
        url = "https://oapi.dingtalk.com/topapi/v2/user/getbymobile"
        data = {"access_token": access_token, "mobile": self.phone, "support_exclusive_account_search": "true"}
        resp = requests.post(url=url, data=data)
        data = resp.json()
        if data.get("errcode"):
            raise ValueError(f"get_user_id fail, response data: {data}, please check your phone number")
        return data.get("result").get("userid")
