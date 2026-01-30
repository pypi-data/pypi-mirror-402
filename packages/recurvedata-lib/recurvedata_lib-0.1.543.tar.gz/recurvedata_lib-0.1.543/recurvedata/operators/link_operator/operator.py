import copy
from typing import Any, Optional

from recurvedata.core.translation import _l
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.task import BaseTask


class ConfigTask(BaseTask):
    pass


class LinkOperator(BaseOperator):
    @classmethod
    def get_link_setting(cls, node_config: dict) -> tuple[int, str, Optional[int]]:
        source = node_config["source"]
        return source["workflow_id"], source["workflow_version_tag"], source.get("link_node_key")

    @classmethod
    def config_schema(cls) -> dict:  # front-end does not use this config schema to show
        return {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "title": _l("Target Workflow"),
                    "description": _l("ID of the workflow to link to"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "workflow_version": {
                    "type": "string",
                    "title": _l("Workflow Version Tag"),
                    "description": _l("Version tag of the target workflow (e.g. latest, v1.0)"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "node_id": {
                    "type": "string",
                    "title": _l("Target Node"),
                    "description": _l("ID of the node to link to in the target workflow"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "variables": {
                    "type": "string",
                    "title": _l("Custom Variables"),
                    "default": "{}",
                    "description": _l("Custom variables to pass to the linked workflow in JSON format"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "json",
                    },
                },
            },
            "required": [
                "workflow_id",
                "workflow_version",
            ],
        }

    def execute(self):
        from recurvedata.executors import LinkExecutor

        link_custom_variables = self.get_link_custom_variables(
            self.dag, self.node, self.execution_date, self.variables, self.node.job_variable
        )
        link_settings = self.node.link_settings
        link_executor = LinkExecutor(
            self.dag,
            self.node,
            execution_date=self.execution_date,
            link_workflow_id=link_settings["workflow_id"],
            link_node_id=link_settings["node_id"],
            custom_variables=link_custom_variables,
            is_link_workflow=link_settings["is_link_workflow"],
        )
        # TODO(chenjingmeng): temporary solution to distinguish link operator
        link_executor.node.is_link_op = True
        link_executor.node.origin_node = self.node
        link_executor.run()

    @classmethod
    def validate(cls, configuration) -> dict:
        return configuration  # variables is dict type which will fail the json validation

    def run_stage(self, stage):
        return self.execute()

    @classmethod
    def ui_config_to_config(cls, configuration: dict[str, Any]) -> dict[str, Any]:
        source = configuration["source"]
        source["variables"] = configuration.get("variables", {})
        return source

    @classmethod
    def get_link_custom_variables(cls, dag, node, execution_date, variables, job_variables: dict):
        # if linkOp has not configured the variables, use job_variables https://project.feishu.cn/recurvedata/issue/detail/5342288226
        link_variables = copy.deepcopy(job_variables) if job_variables else {}
        task_obj = ConfigTask(dag, node, execution_date, variables)
        link_custom_variables = task_obj.rendered_config["variables"]

        if "execution_date" in variables and "execution_date" not in link_custom_variables:
            # user may update `execution_date` in variable, which may not appear in link custom variable,
            # so we need to pass the updated `execution_date` to link
            link_custom_variables["execution_date"] = variables["execution_date"]
        link_variables.update(link_custom_variables)
        return link_variables

    @classmethod
    def get_ds_name_field_values(cls, rendered_config: dict) -> list[str]:
        # todo: check linked node
        return []
