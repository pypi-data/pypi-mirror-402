import re

from recurvedata.consts import ConnectionCategory, ConnectorGroup

try:
    from pandas import DataFrame
except ImportError:
    pass

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.connectors.const import LoadMode
from recurvedata.connectors.proxy import HTTP_PROXY_CONFIG_SCHEMA, HttpProxyMixin
from recurvedata.core.translation import _l

CONNECTION_TYPE = "google_service_account"
UI_CONNECTION_TYPE = "Google Service Account"

try:
    import gspread  # noqa
    import pandas as pd
    from google.oauth2 import service_account
    from gspread.worksheet import Worksheet  # noqa
except ImportError:
    pass


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class GoogleServiceAccount(HttpProxyMixin, RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    category = [ConnectionCategory.SERVICE]
    setup_extras_require = [
        "google-auth",
    ]
    # gspread 暂时不加到 setup_extras_require 里，而是加到 operator 的 setup 里
    default_timeout = 120

    config_schema = {
        "type": "object",
        "properties": {
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
            "universe_domain": {
                "type": "string",
                "title": _l("Universe Domain"),
                "default": "googleapis.com",
            },
            "proxies": HTTP_PROXY_CONFIG_SCHEMA["proxies"],
        },
        "order": [
            "project_id",
            "private_key_id",
            "private_key",
            "client_email",
            "client_id",
            "auth_uri",
            "token_uri",
            "auth_provider_x509_cert_url",
            "client_x509_cert_url",
            "universe_domain",
            "proxies",
        ],
        "required": [
            "project_id",
            "private_key_id",
            "private_key",
            "client_email",
        ],
        "secret": [
            "private_key",
        ],
    }

    def init_credential_key_dict(self):
        self.private_key = self._convert_private_key(self.private_key)
        _key_dict = {
            "type": "service_account",
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key,
            "client_email": self.client_email,
            "auth_uri": self.auth_uri,
            "token_uri": self.token_uri,
            "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
            "client_x509_cert_url": self.client_x509_cert_url,
            "universe_domain": self.universe_domain,
        }
        if self.client_id:
            _key_dict["client_id"] = self.client_id
        return _key_dict

    def init_credential(self):
        credentials = service_account.Credentials.from_service_account_info(info=self.init_credential_key_dict())
        return credentials

    @staticmethod
    def _convert_private_key(private_key: str):
        # Depending on how the JSON was formatted, it may contain
        # escaped newlines. Convert those to actual newlines.
        private_key = private_key.replace("\\\n", "\n")
        return private_key.replace("\\n", "\n")

    def test_connection(self):
        # 暂时不校验。如果私钥有问题这里好像会报错
        with self._init_proxy_manager():
            _ = self.init_credential()

    def get_sheet(self, url: str, sheet_gid: int = None):
        """
        不传 sheet_gid，默认返回第一个 sheet
        :param url:
        :param sheet_gid:
        :return:
        """
        with self._init_proxy_manager():
            gc = gspread.service_account_from_dict(self.init_credential_key_dict())
            gc.set_timeout(self.default_timeout)
            spread_sheet = gc.open_by_url(url)
            sheets = spread_sheet.worksheets()
            if sheet_gid is not None:
                for sheet in sheets:
                    if sheet.id == sheet_gid:
                        return sheet
            if sheets:
                return sheets[0]

    def read_sheet_to_df(
        self, sheet: "Worksheet", cell_range: str = None, columns: list[str] = None, dataframe_kwargs: dict = None
    ) -> "pd.DataFrame":
        """
        :param sheet:
        :param cell_range:
            不传的话，默认读取整个 sheet
            传的话，例如 'A1:B5'
        :param columns:
            不传的话，默认取 sheet 第一行作为 columns
            传的话，例如 ['col1', 'col2', 'col3']
        :param dataframe_kwargs:
            pandas.DataFrame 传入的参数
        :return:
        """
        with self._init_proxy_manager():  # todo: use wrapper
            if not cell_range:
                data = sheet.get_all_values()
            else:
                data = sheet.get(cell_range)
            dataframe_kwargs = dataframe_kwargs or {}
            if not columns:
                df = pd.DataFrame(data[1:], columns=data[0], **dataframe_kwargs)
            else:
                df = pd.DataFrame(data, columns=columns, **dataframe_kwargs)
            return df

    @staticmethod
    def parse_sheet_url(url: str) -> (str, int):
        """输入 URL，返回 token 和 sheet id
        :param url: https://docs.google.com/spreadsheets/d/118WyiPGFQ3ni7Gp6oNhZtkc9wEmAPfqAWynvP2ufgPk/edit#gid=1996978628
        :return: ("118WyiPGFQ3ni7Gp6oNhZtkc9wEmAPfqAWynvP2ufgPk", "1996978628")
        """
        from gspread.utils import extract_id_from_url

        spread_sheet_id = extract_id_from_url(url)
        gid_pat = re.compile(r"gid=(?P<gid>\d+)")
        gid_mobj = gid_pat.search(url)
        sheet_id = int(gid_mobj.group("gid")) if gid_mobj else None
        return spread_sheet_id, sheet_id

    def load_df_to_sheet(self, df: DataFrame, sheet: "Worksheet", mode: str, **kwargs):
        """write data to google sheet

        Args:
            sheet (Worksheet):
            df (DataFrame):
            mode (str): OVERWRITE/APPEND
        """
        # Determine the mode and write the data
        headers = df.columns.values.tolist()
        values = df.values.tolist()
        with self._init_proxy_manager():
            self.load_values_to_sheet(headers, values, sheet, mode, **kwargs)

    @staticmethod
    def load_values_to_sheet(headers: list[str], values: list[list], sheet: "Worksheet", mode: str, **kwargs):
        if mode == LoadMode.OVERWRITE:
            sheet.clear()
            sheet.update(
                [
                    headers,
                ]
                + values,
                **kwargs,
            )
        elif mode == LoadMode.APPEND:
            existing_rows = sheet.get_all_values()
            next_row = len(existing_rows) + 1
            sheet.insert_rows(values, row=next_row, **kwargs)
