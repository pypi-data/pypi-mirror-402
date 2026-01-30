import base64
from contextlib import contextmanager
from urllib.parse import urlparse

import httpx

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.connectors.proxy import HTTP_PROXY_CONFIG_SCHEMA, HttpProxyMixin
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "n8n"
UI_CONNECTION_TYPE = "n8n"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class N8N(HttpProxyMixin, RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "title": _l("API Address"),
                "description": _l("The URL of the n8n API, e.g. https://localhost:5678/api/v1"),
            },
            "api_key": {"type": "string", "title": _l("API KEY")},
            "timeout": {
                "type": "number",
                "title": _l("Timeout"),
                "description": _l("The timeout of the n8n API, e.g. 60"),
                "default": 60,
            },
            "webhook_credential": {
                "type": "object",
                "title": _l("Webhook Trigger Node Credential"),
                "description": _l("The credential of the n8n webhook trigger node"),
                "properties": {
                    "credential_type": {
                        "type": "string",
                        "title": _l("Credential Type"),
                        "enum": ["Basic Auth", "Header Auth", "JWT Auth", "None"],
                        "enumNames": ["Basic Auth", "Header Auth", "JWT Auth", "None"],
                        "default": "None",
                    },
                    "basic_auth": {
                        "ui:hidden": '{{parentFormData.credential_type !== "Basic Auth"}}',
                        "type": "object",
                        "title": _l("Basic Auth"),
                        "description": _l("The basic auth of the n8n webhook trigger node"),
                        "properties": {
                            "username": {"type": "string", "title": _l("Username")},
                            "password": {"type": "string", "title": _l("Password")},
                        },
                    },
                    "header_auth": {
                        "ui:hidden": '{{parentFormData.credential_type !== "Header Auth"}}',
                        "type": "object",
                        "title": _l("Header Auth"),
                        "description": _l("The header auth of the n8n webhook trigger node"),
                        "properties": {
                            "header_name": {"type": "string", "title": _l("Header Name")},
                            "header_value": {"type": "string", "title": _l("Header Value")},
                        },
                    },
                    "jwt_auth": {
                        "ui:hidden": '{{parentFormData.credential_type !== "JWT Auth"}}',
                        "type": "object",
                        "title": _l("JWT Auth"),
                        "description": _l("The jwt auth of the n8n webhook trigger node"),
                        "properties": {
                            "jwt_token": {"type": "string", "title": _l("JWT Token")},
                        },
                    },
                },
                "order": ["credential_type", "basic_auth", "header_auth", "jwt_auth"],
            },
            "proxies": HTTP_PROXY_CONFIG_SCHEMA["proxies"],
        },
        "order": ["url", "api_key", "timeout", "webhook_credential", "proxies"],
        "required": ["url", "api_key"],
        "secret": [
            "api_key",
            "webhook_credential.basic_auth.password",
            "webhook_credential.header_auth.header_value",
            "webhook_credential.jwt_auth.jwt_token",
        ],
    }

    def test_connection(self):
        pass

    @contextmanager
    def _n8n_client(self) -> httpx.Client:
        with self._init_proxy_manager():
            yield httpx.Client(
                base_url=f"{self.url}", headers={"X-N8N-API-KEY": f"{self.api_key}"}, timeout=self.timeout
            )

    def get_workflows(self) -> list[dict]:
        path = "/workflows"
        workflows = []
        cursor = None
        with self._n8n_client() as client:
            response = client.get(path)
            workflows.extend(response.json()["data"])
            if response.json()["nextCursor"] and response.json()["nextCursor"] != cursor:
                cursor = response.json()["nextCursor"]
                while cursor:
                    response = client.get(path, params={"cursor": cursor})
                    workflows.extend(response.json()["data"])
                    cursor = response.json()["nextCursor"]
            return workflows

    def _trigger_workflow_via_webhook(self, webhook_id: str, payload: dict) -> dict:
        main_url = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"
        webhook_url = f"{main_url}/webhook/{webhook_id}"
        headers = {}
        credential_type = self.webhook_credential.get("credential_type")
        basic_auth = self.webhook_credential.get("basic_auth", {})
        header_auth = self.webhook_credential.get("header_auth", {})
        jwt_auth = self.webhook_credential.get("jwt_auth", {})
        with self._init_proxy_manager():
            if credential_type == "Basic Auth":
                username = basic_auth.get("username", "")
                password = basic_auth.get("password", "")
                headers["Authorization"] = f'Basic {base64.b64encode(f"{username}:{password}".encode()).decode()}'
            elif credential_type == "Header Auth":
                header_name = header_auth.get("header_name", "")
                header_value = header_auth.get("header_value", "")
                headers[header_name] = header_value
            elif credential_type == "JWT Auth":
                jwt_token = jwt_auth.get("jwt_token", "")
                headers["Authorization"] = f"Bearer {jwt_token}"
            response = httpx.post(url=webhook_url, headers=headers, timeout=self.timeout, json=payload)

            return response.json()
