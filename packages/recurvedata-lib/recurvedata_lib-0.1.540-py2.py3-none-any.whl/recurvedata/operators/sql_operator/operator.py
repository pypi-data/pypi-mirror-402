from typing import Any

import jsonschema

from recurvedata.connectors.service import list_sql_operator_types
from recurvedata.core.translation import _l
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.task import BaseTask
from recurvedata.operators.utils import lineage


class SQLTask(BaseTask):
    no_template_fields = ("autocommit", "data_source_name")

    @classmethod
    def config_schema(cls):
        # get_names_by_type = cls.get_connection_names_by_type
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("Data Source"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {"supportTypes": list_sql_operator_types()},
                },
                # "database": {
                #     "type": "string",
                #     "title": _l("Database"),
                #     "ui:field": "CodeEditorWithReferencesField",
                #     "ui:options": {
                #         "type": "plain",
                #     },
                # },
                "sql": {
                    "type": "string",
                    "title": _l("SQL Query"),
                    "description": _l(
                        "Execute single or multiple SQL statements. "
                        "Supports Jinja templating for variables and dynamic queries."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "sql",
                    },
                },
            },
            "required": ["data_source_name", "sql"],
        }

    @classmethod
    def validate(cls, configuration: dict[str, Any]) -> dict[str, Any]:
        config = super().validate(configuration)

        ds = cls.must_get_connection_by_name(configuration["data_source_name"])
        if not ds.is_dbapi:
            raise jsonschema.ValidationError(message="only DBAPI is supported", path=("data_source_name",))
        return config

    def execute_impl(self, *args, **kwargs):
        config = self.rendered_config
        ds = self.get_connection_by_name(config.data_source_name)
        connector = ds.connector
        # if config.database:
        #     connector.database = config.database

        queries = config.sql
        if connector.is_hive():
            # Set spark.app.name to help locate the specific Recurve task in the YARN UI
            queries = f"SET spark.app.name=recurve.{self.dag.name}.{self.node.name};\n{queries}"

        comment = self.get_query_comment_conf()
        annotated_queries = connector.add_leading_comment(queries, comment)

        connector.execute(annotated_queries, autocommit=config.get("autocommit", False))
        return None

    def parse_lineage(self):
        config = self.rendered_config
        ds = self.get_connection_by_name(config.data_source_name)
        if not lineage.supported_recurve_ds_type(ds.ds_type):
            return
        res = lineage.parse_lineage(config.sql, config.database, ds.name, ds.ds_type)
        return res


class SQLOperator(BaseOperator):
    task_cls = SQLTask
