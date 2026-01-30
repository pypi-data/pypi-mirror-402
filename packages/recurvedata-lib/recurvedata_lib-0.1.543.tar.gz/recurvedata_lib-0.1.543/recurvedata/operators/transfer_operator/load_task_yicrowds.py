import logging
import os

import jsonschema
import pandas as pd

from recurvedata.pigeon.schema import Schema
from recurvedata.pigeon.utils import fs

try:
    import pyhive.hive  # noqa see https://github.com/cloudera/impyla/issues/277
    from yicrowds_client.core import YiCrowdsClient
except ImportError:
    pass
from recurvedata.operators.transfer_operator.task import LoadTask

logger = logging.getLogger(__name__)


class YiCrowdsLoadTask(LoadTask):
    def _infer_column(self):
        schema_file = fs.schema_filename(self.filename)
        logger.info("infer column by schema file %s", schema_file)
        if not os.path.exists(schema_file):
            logger.error("file not exists, not able to infer column")
        schema = Schema.load(schema_file)
        columns = []
        for f in schema:
            columns.append(f.name)
        return columns

    def add_column_to_file(self, columns):
        df = pd.read_csv(self.filename, header=None, names=columns)
        df.to_csv(self.filename, index=False)

    def execute_impl(self, *args, **kwargs):
        conf = self.rendered_config
        self.add_column_to_file(self._infer_column())
        environment = conf.get("environment", "prod")
        project_id = conf.get("yc_project_id")
        tag = conf.get("yc_tag")
        no_error = YiCrowdsClient(env=environment).upload_data_local(project_id=project_id, tags=tag, fp=self.filename)
        if not no_error:
            raise Exception("upload_data_local上传异常")

    @classmethod
    def validate(cls, configuration):
        conf = super().validate(configuration)
        environment = conf.get("environment", "prod")
        project_id = conf.get("yc_project_id")
        tag = conf.get("yc_tag")

        yca = YiCrowdsClient(env=environment)
        if not yca.if_project_id_exists(project_id=project_id):
            raise jsonschema.ValidationError(
                message=f"YiCrowds Project ID: {project_id} does not exist", path=("yc_project_id",)
            )

        if yca.if_tag_exists(project_id=project_id, tags=tag, is_regex=conf.get("is_regex")):
            raise jsonschema.ValidationError(
                message=f"YiCrowds Tag: {tag} exist", path=("yc_tag", "yc_project_id", "is_regex")
            )

    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "environment": {
                    "type": "string",
                    "title": "Environment",
                    "enum": ["prod", "dev"],
                    "enumNames": ["prod", "dev"],
                    "default": "prod",
                    "description": "YiCrowds 有正式环境和测试环境，默认正式环境",
                },
                "yc_project_id": {
                    "type": "string",
                    "title": "YiCrowds Project ID",
                    "description": "YiCrowds项目ID，可以通过URL地址获取",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "yc_tag": {
                    "type": "string",
                    "title": "YiCrowds Tag",
                    "description": "需要写入数据的tag",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
            },
            "required": ["yc_project_id", "yc_tag"],
        }
