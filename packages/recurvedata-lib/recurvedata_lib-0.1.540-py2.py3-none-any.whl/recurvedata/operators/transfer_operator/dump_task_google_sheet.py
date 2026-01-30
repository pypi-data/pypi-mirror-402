import logging

try:
    import pandas as pd
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.dump_sheet_task_base import SheetDumpTaskBase

logger = logging.getLogger(__name__)


class GoogleSheetDumpTask(SheetDumpTaskBase):
    _AUTO_REGISTER = True
    ds_name_fields = ("google_service_account",)
    worker_install_require = [
        "gspread",
    ]

    custom_config_schema_properties = {
        "google_service_account": {
            "type": "string",
            "title": _l("Service Account"),
            "description": _l("Google service account with permissions to access the spreadsheet"),
            "ui:field": "ProjectConnectionSelectorField",
            "ui:options": {
                "supportTypes": [
                    "google_service_account",
                ],
            },
        },
        "file_url": {
            "type": "string",
            "title": _l("Spreadsheet URL"),
            "description": _l("URL of the Google spreadsheet (defaults to first sheet if no sheet ID specified)"),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
        "cell_range": {
            "type": "string",
            "title": _l("Data Range"),
            "description": _l("Cell range in A1 notation (e.g. A1:B10). Reads entire sheet if empty"),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
    }
    custom_config_schema_required = ["google_service_account", "file_url"]

    def read_origin_df(self) -> "pd.DataFrame":
        conf = self.rendered_config

        ds = self.must_get_connection_by_name(conf.google_service_account)
        service_account = ds.recurve_connector
        spread_sheet_id, sheet_id = service_account.parse_sheet_url(conf.file_url)
        logger.info(f"reading {conf.file_url}, gid {sheet_id}")

        sheet = service_account.get_sheet(conf.file_url, sheet_id)
        df = service_account.read_sheet_to_df(sheet, cell_range=conf.cell_range)
        logger.info(f"original DataFrame shape {df.shape}, dtypes:\n{df.dtypes}")
        logger.info(df.head())
        return df
