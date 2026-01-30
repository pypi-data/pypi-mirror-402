"""Kafka sink task for Flink CDC streaming"""

import logging

from recurvedata.core.translation import _l
from recurvedata.operators.stream_operator.const import CDC_FORMAT_DEBEZIUM, SINK_TYPE_KAFKA
from recurvedata.operators.stream_operator.task import StreamSinkTask

logger = logging.getLogger(__name__)


class KafkaSinkTask(StreamSinkTask):
    """
    Kafka sink task for streaming CDC data to message queue.

    Supports:
    - Apache Kafka 0.11+, 1.x, 2.x, 3.x
    - Confluent Kafka
    - Amazon MSK

    Features:
    - Multiple CDC formats (Debezium, Canal, Maxwell)
    - Dynamic topic naming
    - SASL/SSL authentication
    - At-least-once semantics

    Docs: https://nightlies.apache.org/flink/flink-cdc-docs-release-3.5/docs/connectors/pipeline-connectors/kafka/
    """

    ds_name_fields = ("connection_name",)
    worker_install_require = []

    def build_sink_config(self) -> dict:
        """Build Kafka sink configuration for Flink CDC YAML"""
        # Get Flink connection (which includes Kafka config)
        connection = self.must_get_connection_by_name(self.config["connection_name"])

        # Extract Kafka bootstrap servers from Flink connection
        kafka_bootstrap_servers = connection.data.get("kafka_bootstrap_servers", "localhost:9092")

        config = {
            "type": SINK_TYPE_KAFKA,
            "properties.bootstrap.servers": kafka_bootstrap_servers,
            "topic": self.config.get("topic", "reorc-cdc-${schemaName}-${tableName}"),
            "format": CDC_FORMAT_DEBEZIUM,  # Always use Debezium format
        }

        # Add Kafka security if configured
        if connection.data.get("kafka_security_protocol"):
            config["properties.security.protocol"] = connection.data["kafka_security_protocol"]
            config["properties.sasl.mechanism"] = connection.data.get("kafka_sasl_mechanism", "PLAIN")

            if connection.data.get("kafka_jaas_config"):
                config["properties.sasl.jaas.config"] = connection.data["kafka_jaas_config"]

        # Optional: Partitions
        if self.config.get("partitions"):
            config["sink.partitions"] = self.config["partitions"]

        # Optional: Delivery guarantee
        if self.config.get("delivery_guarantee"):
            config["sink.delivery-guarantee"] = self.config["delivery_guarantee"]

        return config

    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "connection_name": {
                    "type": "string",
                    "title": _l("Flink Connection (with Kafka)"),
                    "description": _l("Select Flink connection that includes Kafka configuration"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": ["Apache Flink"],
                    },
                },
                "topic": {
                    "type": "string",
                    "title": _l("Kafka Topic Pattern"),
                    "default": "reorc-cdc-${schemaName}-${tableName}",
                    "description": _l(
                        "Kafka topic pattern. Use placeholders:\n"
                        "- ${databaseName} - source database name\n"
                        "- ${schemaName} - source schema name\n"
                        "- ${tableName} - source table name\n"
                        "Examples:\n"
                        "- reorc-cdc-${tableName}\n"
                        "- ${databaseName}.${tableName}\n"
                        "- events-${schemaName}-${tableName}"
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "partitions": {
                    "type": "number",
                    "title": _l("Number of Partitions"),
                    "description": _l(
                        "Number of Kafka topic partitions (optional, uses Kafka default if not specified)"
                    ),
                    "minimum": 1,
                    "maximum": 1000,
                    "ui:options": {"controls": False},
                },
                "delivery_guarantee": {
                    "type": "string",
                    "title": _l("Delivery Guarantee"),
                    "default": "at-least-once",
                    "enum": ["at-least-once", "exactly-once", "none"],
                    "enumNames": [
                        "At-least-once (recommended)",
                        "Exactly-once (transactional)",
                        "None (best effort)",
                    ],
                    "description": _l("Kafka delivery guarantee level"),
                },
            },
            "required": ["connection_name"],
        }
