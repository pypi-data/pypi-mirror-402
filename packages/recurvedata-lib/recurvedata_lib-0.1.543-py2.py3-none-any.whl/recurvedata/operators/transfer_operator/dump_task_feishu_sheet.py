import json
import logging
import urllib.parse

try:
    import pandas as pd

    from recurvedata.pigeon.connector.feishu import FeishuBot
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.dump_sheet_task_base import SheetDumpTaskBase

logger = logging.getLogger(__name__)


class FeishuSheetDumpTask(SheetDumpTaskBase):
    _AUTO_REGISTER = True
    ds_name_fields = ("feishu_bot",)
    worker_install_require = ["pandas", "numpy", "pigeon[feishu]"]

    custom_config_schema_properties = {
        "feishu_bot": {
            "type": "string",
            "title": _l("Feishu Bot Connection"),
            "description": _l(
                "Select the Feishu bot connection that has permissions to access and read the target sheet"
            ),
            "ui:field": "ProjectConnectionSelectorField",
            "ui:options": {
                "supportTypes": [
                    "feishu_bot",
                ],
            },
            # 'default': cls.first_or_default(dss, ''),
        },
        "file_url": {
            "type": "string",
            "title": _l("Feishu Document URL"),
            "description": _l(
                "URL of the Feishu spreadsheet or document to read data from. For multi-sheet documents, the first sheet will be used by default unless a specific sheet ID is included in the URL"
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
        "cell_range": {
            "type": "string",
            "title": _l("Data Range"),
            "description": _l(
                "Optional range of cells to read in A1 notation (e.g. A1:D100). Leave empty to read all data from the sheet"
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
    }
    custom_config_schema_required = ["feishu_bot", "file_url"]

    def read_origin_df(self) -> "pd.DataFrame":
        conf = self.rendered_config
        if conf.extra_read_kwargs:
            extra_read_kwargs = json.loads(conf.extra_read_kwargs)
        else:
            extra_read_kwargs = {}

        ds = self.must_get_connection_by_name(conf.feishu_bot)
        bot = FeishuBot(**ds.extra)
        file_type, file_token, sheet = self.parse_feishu_sheets_url(conf.file_url)
        logger.info(f"reading {conf.file_url}")
        if file_type == "file":
            df = bot.read_feishuexcel(file_token, **extra_read_kwargs)
        else:  # sheets
            if not sheet:
                logger.info("sheet_id not found in url, use the first sheet as default")
                sheet_ids, _ = bot.get_sheet_ids(file_token)
                sheet = sheet_ids[0]
            if conf.cell_range:
                sheet = f"{sheet}!{conf.cell_range}"
            df = bot.read_feishusheet(file_token, sheet, **extra_read_kwargs)

        logger.info(f"original DataFrame shape {df.shape}, dtypes:\n{df.dtypes}")
        logger.info(df.head())
        return df

    @staticmethod
    def parse_feishu_sheets_url(url: str) -> tuple[str, str, str]:
        rv = urllib.parse.urlparse(url)
        if "/file/" in url:
            file_type = "file"
        elif "/sheets/" in url:
            file_type = "sheets"
        elif "/wiki/" in url:
            file_type = "wiki"
        else:
            raise ValueError(f"unsupported url {url}")

        file_token = rv.path.rsplit("/", 1)[-1]
        sheet = urllib.parse.parse_qs(rv.query).get("sheet") or None
        if sheet:
            sheet = sheet[0]

        bot = FeishuBot()
        if file_type == "wiki":
            obj_type, obj_token = bot.get_wiki_type_token(wiki_token=file_token)
            if obj_type == "sheet":
                file_type, file_token = obj_type, obj_token
            else:
                raise ValueError(f"unsupported url {url}")

        return file_type, file_token, sheet
