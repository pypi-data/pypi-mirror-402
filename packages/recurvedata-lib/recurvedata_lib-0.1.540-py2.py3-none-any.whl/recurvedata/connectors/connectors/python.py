from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "python"
UI_CONNECTION_TYPE = "Python"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class Python(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE

    group = [ConnectorGroup.DESTINATION]
    test_required = False
    config_schema = {
        "type": "object",
        "properties": {
            "python_version": {
                "type": "string",
                "title": _l("Python Version"),
                "enum": ["3.11.11"],
                "enumNames": ["3.11.11"],
                "default": "3.11.11",
            },
            "pyenv": {
                "type": "string",
                "title": _l("Python Virtual Environment Name"),
                "default": "recurve_executor",
            },
            "requirements": {
                "type": "string",
                "title": _l("Python Package Requirements"),
                "description": _l(
                    "List of Python packages and versions to install, the same format as requirements.txt"
                ),
                "ui:options": {
                    "type": "textarea",
                    "rows": 10,
                },
            },
        },
        "order": ["python_version", "pyenv", "requirements"],
        "required": ["python_version", "pyenv"],
        "secret": [],
    }

    def test_connection(self):
        pass
