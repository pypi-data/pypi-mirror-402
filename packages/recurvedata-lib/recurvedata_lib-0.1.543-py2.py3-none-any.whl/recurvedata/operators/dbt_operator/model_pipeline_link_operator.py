from recurvedata.core.translation import _l
from recurvedata.operators.link_operator import LinkOperator


class LinkModelPipelineOperator(LinkOperator):
    @classmethod
    def config_schema(cls) -> dict:  # front-end does not use this config schema to show
        return {
            "type": "object",
            "properties": {
                "model_pipeline_id": {
                    "type": "string",
                    "title": _l("Model Pipeline ID"),
                    "description": _l("Model Pipeline ID"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "workflow_id": {
                    "type": "string",
                    "title": _l("Workflow ID"),
                    "description": _l("Workflow ID"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "workflow_version": {
                    "type": "string",
                    "title": _l("Workflow Version"),
                    "description": _l("Workflow Version"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "variables": {
                    "type": "string",
                    "title": _l("Variables"),
                    "default": "{}",
                    "description": _l("Variables in JSON format"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "json",
                    },
                },
            },
            "required": [
                "model_pipeline_id",
                "workflow_id",
                "workflow_version",
            ],
        }
