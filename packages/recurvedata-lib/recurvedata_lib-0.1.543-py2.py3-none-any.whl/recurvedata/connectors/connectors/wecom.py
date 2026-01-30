from urllib.parse import urlparse

import requests

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "wecom"
UI_CONNECTION_TYPE = "WeCom"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class WeCom(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.INTEGRATION]

    config_schema = {
        "type": "object",
        "properties": {
            "webhook_url": {"type": "string", "title": _l("WeCom Webhook URL")},
        },
        "order": [
            "webhook_url",
        ],
        "required": [
            "webhook_url",
        ],
    }

    @property
    def webhook_url(self):
        return self.conf["webhook_url"]

    @property
    def wecom_conf(self):
        if hasattr(self, "_wecom_conf"):
            return self._wecom_conf
        self.init_config()
        return self._wecom_conf

    def test_connection(self):
        """
        Test WeCom webhook connection.
        Validate URL format and network connectivity without sending actual messages.
        """
        # Validate URL format
        parsed_url = urlparse(self.webhook_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid webhook URL format")

        if parsed_url.scheme != "https":
            raise ValueError("WeCom webhook URL must use HTTPS")

        # Verify WeCom domain
        if "qyapi.weixin.qq.com" not in parsed_url.netloc:
            raise ValueError("Invalid WeCom webhook URL domain")

        # Test network connectivity (use HEAD request without sending message body)
        try:
            requests.head(self.webhook_url, timeout=10, allow_redirects=True)
            # Connection test only, status code not checked (HEAD may return 405)
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to WeCom webhook: {str(e)}")
