from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.object_store import ObjectStoreMixin
from recurvedata.connectors.proxy import HTTP_PROXY_CONFIG_SCHEMA, HttpProxyMixin
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "google_cloud_storage"
UI_CONNECTION_TYPE = "Google Cloud Storage"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class GoogleCloudStorage(HttpProxyMixin, ObjectStoreMixin):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = []
    group = [ConnectorGroup.DESTINATION]
    test_required = False

    config_schema = {
        "type": "object",
        "properties": {
            "key_dict": {
                "type": "object",
                "title": _l("Service Account Key"),
                "description": _l("Google Cloud service account key credentials"),
                "properties": {
                    "type": {
                        "type": "string",
                        "title": _l("Account Type"),
                        "default": "service_account",
                    },
                    "project_id": {"type": "string", "title": _l("Google Cloud Project ID")},
                    "private_key_id": {"type": "string", "title": _l("Google Auth Private Key ID")},
                    "private_key": {
                        "type": "string",
                        "title": _l("Google Auth Private Key"),
                        "ui:options": {"type": "textarea"},
                    },
                    "client_email": {"type": "string", "title": _l("Service Account Email")},
                    "client_id": {"type": "string", "title": _l("Google OAuth Client ID")},
                    "auth_uri": {
                        "type": "string",
                        "title": _l("Google OAuth Auth URI"),
                        "default": "https://accounts.google.com/o/oauth2/auth",
                    },
                    "token_uri": {
                        "type": "string",
                        "title": _l("Google OAuth Token URI"),
                        "default": "https://oauth2.googleapis.com/token",
                    },
                    "auth_provider_x509_cert_url": {
                        "type": "string",
                        "title": _l("Google OAuth Certificate URL (Auth Provider)"),
                        "default": "https://www.googleapis.com/oauth2/v1/certs",
                    },
                    "client_x509_cert_url": {
                        "type": "string",
                        "title": _l("Google OAuth Certificate URL (Client)"),
                        "default": "https://www.googleapis.com/robot/v1/metadata/x509/recurvedata-gcs%40brand-portal-prod.iam.gserviceaccount.com",
                    },
                },
                "order": [
                    "type",
                    "project_id",
                    "private_key_id",
                    "private_key",
                    "client_email",
                    "client_id",
                    "auth_uri",
                    "token_uri",
                    "auth_provider_x509_cert_url",
                    "client_x509_cert_url",
                ],
                "required": [
                    "type",
                    "project_id",
                    "private_key_id",
                    "private_key",
                    "client_id",
                ],
                "secret": [
                    "private_key",
                ],
            },
            "bucket": {
                "type": "string",
                "title": _l("Bucket Name"),
                "description": _l("Name of the Google Cloud Storage bucket"),
            },
            "proxies": HTTP_PROXY_CONFIG_SCHEMA["proxies"],
        },
        "order": [
            "key_dict",
            "bucket",
            "proxies",
        ],
        "required": [
            "key_dict",
        ],
        "secret": [
            "key_dict.private_key",
        ],
    }

    def init_connection(self, conf):
        self.connector = None  # todo

    def test_connection(self):
        # todo
        pass

    juice_sync_able = True

    def juice_sync_path(self, path: str) -> str:
        return f"gcs://{path}"  # todo
