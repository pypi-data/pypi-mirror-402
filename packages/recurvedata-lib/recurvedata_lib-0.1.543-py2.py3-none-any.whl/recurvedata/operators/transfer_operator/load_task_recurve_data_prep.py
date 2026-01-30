import logging
import os

from recurvedata.operators.context import context

try:
    from recurvedata.pigeon.utils import fs
except ImportError:
    pass

from recurvedata.operators.transfer_operator.task import LoadTask

logger = logging.getLogger(__name__)


class DataPrepLoadTask(LoadTask):
    should_write_header = True
    enabled = False

    def _rename_filename_to_csv(self):
        filename2 = self.filename + ".csv"
        if not os.path.exists(filename2):
            if os.path.exists(self.filename):
                os.rename(self.filename, filename2)
        self.filename = filename2

    def execute_impl(self, *args, **kwargs):
        self._rename_filename_to_csv()
        if fs.is_file_empty(self.filename):
            logger.warning("file %s not exists or has no content, skip.", self.filename)
            return

        conf = self.rendered_config
        context.client.upload_file_to_data_preparation(
            project_id=conf.get("project_id") and int(conf["project_id"]),
            file_name=self.filename,
            table_id=conf.get("table_id") and int(conf["table_id"]),
            import_strategy=conf.get("import_strategy"),
            keep_user_modified_data=conf.get("keep_user_modified_data"),
            publish=conf.get("publish"),
        )

    @classmethod
    def config_schema(cls):
        schema = {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "title": "Project ID"},
                "table_id": {
                    "type": "string",
                    "title": "Table ID",
                },
                "keep_user_modified_data": {
                    "type": "boolean",
                    "title": "Keep User Modified Data",
                    "default": False,
                    "description": "是否保留用户修改的数据",
                },
                "import_strategy": {
                    "type": "string",
                    "title": "Import Strategy",
                    "description": "导入策略",
                    "enum": ["overwrite", "replace", "merge"],
                    "enumNames": ["overwrite", "replace", "merge"],
                },
                "publish": {
                    "type": "boolean",
                    "title": "Publish",
                    "default": False,
                    "description": "是否发布",
                },
            },
            "required": ["project_id", "table_id"],
        }
        return schema
