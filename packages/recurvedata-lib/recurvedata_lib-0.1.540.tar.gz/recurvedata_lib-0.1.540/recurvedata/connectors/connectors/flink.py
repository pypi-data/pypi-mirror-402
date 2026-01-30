import logging

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    logger.error("httpx library not installed")
    httpx = None

try:
    from confluent_kafka.admin import AdminClient
except ImportError:
    logger.error("confluent-kafka library not installed")
    AdminClient = None

CONNECTION_TYPE = "flink"
UI_CONNECTION_TYPE = "Apache Flink"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class FlinkConnector(RecurveConnectorBase):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    category = [ConnectionCategory.OTHERS]
    group = [ConnectorGroup.DESTINATION]
    test_required = True
    setup_extras_require = ["httpx>=0.24.0", "confluent-kafka>=2.0.0"]

    config_schema = {
        "type": "object",
        "properties": {
            # Flink Configuration
            "flink_url": {
                "type": "string",
                "title": _l("Flink Server"),
                "description": _l("e.g., http://localhost:8081"),
                "default": "http://localhost:8081",
            },
            "flink_sql_gateway_port": {
                "type": "number",
                "title": _l("Flink SQL Gateway Port"),
                "description": _l("SQL Gateway REST API port"),
                "default": 10000,
            },
            # Kafka Configuration
            "kafka_bootstrap_servers": {
                "type": "string",
                "title": _l("Kafka Bootstrap Servers"),
                "description": _l("e.g., pkc-xxxxx.region.confluent.cloud:9092 or localhost:9092"),
                "default": "localhost:9092",
            },
            "kafka_security_enabled": {
                "type": "boolean",
                "title": _l("Enable Kafka Security (SASL/SSL)"),
                "default": False,
            },
            "kafka_sasl_mechanism": {
                "type": "string",
                "title": _l("SASL Mechanism"),
                "description": _l("e.g., PLAIN, SCRAM-SHA-256, SCRAM-SHA-512"),
                "enum": ["PLAIN", "SCRAM-SHA-256", "SCRAM-SHA-512"],
                "default": "PLAIN",
                "ui:hidden": "{{parentFormData.kafka_security_enabled !== true}}",
            },
            "kafka_sasl_username": {
                "type": "string",
                "title": _l("Kafka API Key / Username"),
                "description": _l("e.g., IIFNGPAIQ7DZ54G7"),
                "ui:hidden": "{{parentFormData.kafka_security_enabled !== true}}",
            },
            "kafka_sasl_password": {
                "type": "string",
                "title": _l("Kafka API Secret / Password"),
                "description": _l("Kafka credentials"),
                "ui:hidden": "{{parentFormData.kafka_security_enabled !== true}}",
            },
        },
        "order": [
            "flink_url",
            "flink_sql_gateway_port",
            "kafka_bootstrap_servers",
            "kafka_security_enabled",
            "kafka_sasl_mechanism",
            "kafka_sasl_username",
            "kafka_sasl_password",
        ],
        "required": ["flink_url", "flink_sql_gateway_port", "kafka_bootstrap_servers"],
        "secret": ["kafka_sasl_password"],
    }

    def get_flink_gateway_url(self) -> str:
        """Get Flink SQL Gateway base URL from flink_url and port"""
        flink_url = self.conf.get("flink_url", "http://localhost:8081")
        # Extract protocol and host from flink_url
        if "://" in flink_url:
            protocol, host_part = flink_url.split("://", 1)
            host = host_part.rstrip("/")
        else:
            protocol = "http"
            host = flink_url.rstrip("/")

        port = self.conf.get("flink_sql_gateway_port", 10000)
        return f"{protocol}://{host.split(':')[0]}:{port}"

    def test_connection(self):
        """Test Flink SQL Gateway, Kafka, and Debezium connector connectivity"""
        logger.info("Starting Flink connector connection test")
        errors = []

        # Test Flink SQL Gateway using /v1/info endpoint
        logger.info("Testing Flink SQL Gateway connectivity")
        if httpx is None:
            logger.error("httpx library not installed")
            errors.append("httpx not installed")
        else:
            try:
                gateway_url = self.get_flink_gateway_url()
                logger.info(f"Connecting to Flink SQL Gateway: {gateway_url}/v1/info")

                with httpx.Client(timeout=10.0) as client:
                    # Test SQL Gateway info endpoint
                    response = client.get(f"{gateway_url}/v1/info")
                    response.raise_for_status()
                    logger.info(f"Flink SQL Gateway connected successfully (status: {response.status_code})")
            except Exception as e:
                logger.error(f"Flink SQL Gateway connection failed: {str(e)}")
                errors.append(f"Flink SQL Gateway: {str(e)}")

        # Test Kafka connectivity (with or without security)
        kafka_bootstrap = self.conf.get("kafka_bootstrap_servers")
        if kafka_bootstrap:
            logger.info("Testing Kafka connectivity")
            if AdminClient is None:
                logger.error("confluent-kafka library not installed")
                errors.append("confluent-kafka not installed")
            else:
                admin_client = None
                try:
                    # Remove protocol prefix if present (Kafka expects host:port format)
                    kafka_servers = kafka_bootstrap.split("://")[-1]
                    logger.info(f"Connecting to Kafka bootstrap servers: {kafka_servers}")

                    admin_config = {
                        "bootstrap.servers": kafka_servers,
                        # Set short timeouts for connection testing
                        "socket.timeout.ms": 5000,  # 5 seconds socket timeout
                        "socket.connection.setup.timeout.ms": 5000,  # 5 seconds for initial connection setup
                        "request.timeout.ms": 5000,  # 5 seconds request timeout
                        "connections.max.idle.ms": 10000,  # 10 seconds max idle
                        "metadata.max.age.ms": 5000,  # 5 seconds metadata refresh
                        "reconnect.backoff.ms": 50,  # Fast backoff for test
                        "reconnect.backoff.max.ms": 1000,  # Max 1 second backoff
                    }

                    # Add security config if enabled
                    security_enabled = self.conf.get("kafka_security_enabled")
                    if security_enabled:
                        sasl_mechanism = self.conf.get("kafka_sasl_mechanism", "PLAIN")
                        sasl_username = self.conf.get("kafka_sasl_username", "")
                        logger.info(
                            f"Kafka security enabled: SASL_SSL with {sasl_mechanism}, username: {sasl_username}"
                        )
                        admin_config.update(
                            {
                                "security.protocol": "SASL_SSL",
                                "sasl.mechanisms": sasl_mechanism,
                                "sasl.username": sasl_username,
                                "sasl.password": self.conf.get("kafka_sasl_password", ""),
                            }
                        )
                    else:
                        logger.info("Kafka security disabled, using plain connection")

                    admin_client = AdminClient(admin_config)
                    logger.info("Listing Kafka topics (timeout: 5s)...")
                    topics = admin_client.list_topics(timeout=5)
                    topic_count = len(topics.topics)
                    logger.info(f"Kafka connected successfully, found {topic_count} topics")
                except Exception as e:
                    logger.error(f"Kafka connection failed: {str(e)}")
                    errors.append(f"Kafka: {str(e)}")
                finally:
                    # Explicitly clean up AdminClient to stop background threads
                    if admin_client is not None:
                        del admin_client
        else:
            logger.info("Kafka bootstrap servers not configured, skipping Kafka test")

        if errors:
            logger.error(f"Connection test failed with {len(errors)} error(s): {' | '.join(errors)}")
            raise ValueError(" | ".join(errors))

        logger.info("Connection test completed successfully")
        return True
