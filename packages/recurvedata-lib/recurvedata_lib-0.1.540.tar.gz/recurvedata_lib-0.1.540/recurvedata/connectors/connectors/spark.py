import json

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "spark"
UI_CONNECTION_TYPE = "Spark"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class SparkSubmit(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    category = [
        ConnectionCategory.DATABASE,
    ]
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "submitter": {
                "type": "string",
                "title": _l("Spark Submit Command"),
                "description": _l("Path to spark-submit executable"),
                "default": "spark-submit",
            },
            "env": {
                "type": "object",
                "title": _l("Environment Variables"),
                "description": _l("Environment variables required for Spark execution"),
                "properties": {
                    "JAVA_HOME": {"type": "string", "title": "JAVA_HOME"},
                    "PYSPARK_PYTHON": {"type": "string", "title": "PYSPARK_PYTHON"},
                    "PYSPARK_DRIVER_PYTHON": {"type": "string", "title": "PYSPARK_DRIVER_PYTHON"},
                    "HADOOP_USER_NAME": {"type": "string", "title": "HADOOP_USER_NAME"},
                    "PIGEON_SECRET_KEY": {"type": "string", "title": "PIGEON_SECRET_KEY"},
                    "PATH": {"type": "string", "title": "PATH"},
                    "SPARK_CONF_DIR": {"type": "string", "title": "SPARK_CONF_DIR"},
                    "HADOOP_CONF_DIR": {"type": "string", "title": "HADOOP_CONF_DIR"},
                    "HIVE_CONF_DIR": {"type": "string", "title": "HIVE_CONF_DIR"},
                    "HIVE_HOME": {"type": "string", "title": "HIVE_HOME"},
                },
                "order": [
                    "JAVA_HOME",
                    "PYSPARK_PYTHON",
                    "PYSPARK_DRIVER_PYTHON",
                    "HADOOP_USER_NAME",
                    "PIGEON_SECRET_KEY",
                    "PATH",
                    "HIVE_CONF_DIR",
                    "HADOOP_CONF_DIR",
                    "SPARK_CONF_DIR",
                    "HIVE_HOME",
                ],
            },
            "execution_config": {
                "type": "object",
                "title": _l("Execution Configuration"),
                "description": _l("Spark execution settings"),
                "properties": {
                    "queue": {
                        "type": "string",
                        "title": _l("Queue Name"),
                        "description": _l("Name of the queue to submit Spark job"),
                        "default": "recurve",
                    },
                    "conf": {
                        "type": "string",
                        "title": _l("Additional Configuration"),
                        "description": _l("Additional Spark configuration in JSON format"),
                        "ui:options": {"type": "textarea"},
                    },
                },
                "order": ["queue", "conf"],
            },
        },
        "order": ["submitter", "env", "execution_config"],
        "required": [
            "submitter",
        ],
        "secret": [],
    }

    def test_connection(self):
        pass

    @staticmethod
    def preprocess_conf(data):
        data = RecurveConnectorBase.preprocess_conf(data)
        execution_config = data.get("execution_config")
        if execution_config:
            execution_config_conf = execution_config.get("conf")
            if execution_config_conf and isinstance(execution_config_conf, str):
                execution_config_conf = json.loads(execution_config_conf)
                execution_config["conf"] = execution_config_conf
        return data
