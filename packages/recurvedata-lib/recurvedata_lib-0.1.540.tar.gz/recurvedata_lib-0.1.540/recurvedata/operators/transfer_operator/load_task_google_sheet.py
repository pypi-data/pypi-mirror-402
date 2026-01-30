import csv
import logging
from typing import Any

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.pigeon.utils import fs

logger = logging.getLogger(__name__)
GOOGLE_SHEET_MAX_ROWS = 1000000
GOOGLE_SHEET_MAX_COLUMNS = 18278


class GoogleSheetLoadTask(LoadTask):
    ds_name_fields = ("google_service_account",)
    should_write_header = True
    worker_install_require = ["gspread"]

    @staticmethod
    def check_csv_content(filename: str) -> tuple[int, int]:
        """Check if the CSV file row and column counts exceed the maximum allowed limits for Google Sheets."""
        row_count = 0
        col_count = 0
        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                row_count += 1
                if row_count == 1:
                    col_count = len(row)
                    if col_count > GOOGLE_SHEET_MAX_COLUMNS:
                        raise ValueError(
                            f"CSV file contains {col_count} columns, which exceeds the maximum allowed "
                            f"{GOOGLE_SHEET_MAX_COLUMNS} columns in Google Sheets."
                        )
                if row_count > GOOGLE_SHEET_MAX_ROWS:
                    raise ValueError(
                        f"CSV file contains {row_count} rows, which exceeds the maximum allowed "
                        f"{GOOGLE_SHEET_MAX_ROWS} rows in Google Sheets."
                    )
        return row_count, col_count

    def execute_impl(self, *args: Any, **kwargs: Any) -> None:
        import pandas as pd

        if fs.is_file_empty(self.filename):
            logger.warning("File %s does not exist or has no content, skipping.", self.filename)
            return

        ds = self.must_get_connection_by_name(self.config["google_service_account"])
        service_account = ds.recurve_connector
        _, sheet_id = service_account.parse_sheet_url(self.config["file_url"])
        sheet = service_account.get_sheet(self.config["file_url"], sheet_id)

        logger.info(f'Loading to {self.config["file_url"]}, gid {sheet_id}')

        # Perform all necessary checks
        csv_row_count, csv_col_count = self.check_csv_content(self.filename)
        current_sheet_rows, current_sheet_cols = sheet.row_count, sheet.col_count

        if self.config["mode"] == const.LOAD_APPEND:
            csv_row_count += current_sheet_rows
            csv_col_count = max(current_sheet_cols, csv_col_count)

        if csv_row_count > GOOGLE_SHEET_MAX_ROWS:
            raise ValueError(
                f"Appending the CSV file will exceed the maximum allowed {GOOGLE_SHEET_MAX_ROWS} rows in Google Sheets."
            )
        if csv_col_count > GOOGLE_SHEET_MAX_COLUMNS:
            raise ValueError(
                f"Appending the CSV file will exceed the maximum allowed {GOOGLE_SHEET_MAX_COLUMNS} columns in Google Sheets."
            )

        # Load the CSV file into a DataFrame after checking the row count
        df = pd.read_csv(self.filename, keep_default_na=False)
        df.fillna("", inplace=True)

        try:
            service_account.load_df_to_sheet(df, sheet, self.config["mode"], value_input_option="USER_ENTERED")
            logger.info(
                f'Data loaded successfully into {self.config["file_url"]}, mode: {self.config["mode"]}, '
                f"rows: {csv_row_count}, cols: {csv_col_count}"
            )
        except Exception as e:
            logger.error(f'Failed to load data into {self.config["file_url"]}: {e}')
            raise

    @classmethod
    def config_schema(cls) -> dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "google_service_account": {
                    "type": "string",
                    "title": _l("Google Service Account Connection"),
                    "description": _l(
                        "Select the Google Service Account connection with write permissions to the target spreadsheet"
                    ),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": ["google_service_account"],
                    },
                },
                "file_url": {
                    "type": "string",
                    "title": _l("Google Sheet URL"),
                    "description": _l(
                        "URL of the target Google Sheet in format: "
                        "https://docs.google.com/spreadsheets/d/{Spreadsheet ID}/edit#gid={Sheet GID}. "
                        "If no sheet GID is specified, the first sheet will be used."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "mode": {
                    "type": "string",
                    "title": _l("Import Mode"),
                    "enum": [const.LOAD_OVERWRITE, const.LOAD_APPEND],
                    "enumNames": [const.LOAD_OVERWRITE, const.LOAD_APPEND],
                    "default": const.LOAD_OVERWRITE,
                    "description": _l(
                        "OVERWRITE: Replace existing data with new data. " "APPEND: Add new data after existing data."
                    ),
                },
            },
            "required": ["google_service_account", "file_url", "mode"],
        }
        return schema
