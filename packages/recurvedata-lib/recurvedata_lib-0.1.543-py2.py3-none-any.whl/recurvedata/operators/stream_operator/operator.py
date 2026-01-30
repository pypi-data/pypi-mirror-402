"""Stream Operator - Real-time data streaming using Apache Flink CDC"""

import logging

from recurvedata.core.translation import _l
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.stream_operator.const import (
    CHECKPOINT_INTERVAL_DEFAULT,
    DEFAULT_PARALLELISM,
    SINK_TYPE_CLICKHOUSE,
    SINK_TYPE_DORIS,
    SINK_TYPE_KAFKA,
    SINK_TYPE_MYSQL,
    SINK_TYPE_POSTGRES,
    SINK_TYPE_STARROCKS,
    SOURCE_TYPE_MYSQL,
    SOURCE_TYPE_POSTGRES,
)

# Import all sink tasks
from recurvedata.operators.stream_operator.sink_task_clickhouse import ClickHouseSinkTask
from recurvedata.operators.stream_operator.sink_task_doris import DorisSinkTask
from recurvedata.operators.stream_operator.sink_task_kafka import KafkaSinkTask
from recurvedata.operators.stream_operator.sink_task_mysql import MySQLSinkTask
from recurvedata.operators.stream_operator.sink_task_postgres import PostgresSinkTask
from recurvedata.operators.stream_operator.sink_task_starrocks import StarRocksSinkTask

# Import all source tasks
from recurvedata.operators.stream_operator.source_task_mysql import MySQLCDCSourceTask
from recurvedata.operators.stream_operator.source_task_postgres import PostgresCDCSourceTask

logger = logging.getLogger(__name__)


class StreamOperator(BaseOperator):
    """
    Real-time streaming operator using Apache Flink CDC.

    Unlike TransferOperator (batch), StreamOperator:
    - Runs continuously (not scheduled)
    - Captures changes in real-time (CDC)
    - Uses Flink instead of Airflow
    - Processes data with sub-second latency

    Architecture:
        Source DB → Flink CDC → Transformation → Target DB/Warehouse

    Supported Sources:
        - MySQL (via Flink CDC MySQL connector)
        - PostgreSQL (via Flink CDC PostgreSQL connector)

    Supported Sinks:
        - Apache Doris
        - StarRocks
        - Kafka
    """

    # Source task mapping - all supported CDC sources
    SOURCE_TASK_MAP = {
        SOURCE_TYPE_MYSQL: MySQLCDCSourceTask,
        SOURCE_TYPE_POSTGRES: PostgresCDCSourceTask,
    }

    # Sink task mapping - all supported sinks
    SINK_TASK_MAP = {
        SINK_TYPE_DORIS: DorisSinkTask,
        SINK_TYPE_STARROCKS: StarRocksSinkTask,
        SINK_TYPE_KAFKA: KafkaSinkTask,
        SINK_TYPE_CLICKHOUSE: ClickHouseSinkTask,
        SINK_TYPE_POSTGRES: PostgresSinkTask,
        SINK_TYPE_MYSQL: MySQLSinkTask,
    }

    def __init__(self, dag, node, execution_date, variables=None):
        super().__init__(dag, node, execution_date, variables)
        self.stream_source_task = None
        self.stream_sink_task = None
        self.transform_sql = None
        self.flink_connection = None

    def init_task(self):
        """Initialize source, sink, and transform tasks"""
        node_config = self.node.config

        # Get Flink connection from flink_config section
        flink_config = node_config.get("flink_config", {})
        flink_conn_name = flink_config.get("flink_connection_name")
        if not flink_conn_name:
            raise ValueError("flink_connection_name is required")

        # Create source task using source_type from config
        source_config = node_config.get("source", {})
        database_type = source_config.get("source_type")
        if not database_type:
            raise ValueError("source source_type is required")

        # Map database type to task class
        database_type_lower = database_type.lower()
        source_task_map = {
            "mysql": MySQLCDCSourceTask,
            "postgres": PostgresCDCSourceTask,
            "postgresql": PostgresCDCSourceTask,
        }

        source_class = source_task_map.get(database_type_lower)
        if not source_class:
            raise ValueError(f"Unsupported source database type: {database_type}")

        # Config is directly in source, not nested under source.config
        self.stream_source_task = source_class(
            dag=self.dag,
            node=self.node,
            execution_date=self.execution_date,
            variables=self.variables,
            config=source_config,
        )

        # Create sink task using database_type from config
        sink_config = node_config.get("sink", {})
        database_type = sink_config.get("source_type")
        if not database_type:
            raise ValueError("sink source_type is required")

        # Map database type to task class
        database_type_lower = database_type.lower()
        sink_task_map = {
            "doris": DorisSinkTask,
            "starrocks": StarRocksSinkTask,
            "kafka": KafkaSinkTask,
            "clickhouse": ClickHouseSinkTask,
            "postgres": PostgresSinkTask,
            "postgresql": PostgresSinkTask,
            "mysql": MySQLSinkTask,
        }

        sink_class = sink_task_map.get(database_type_lower)
        if not sink_class:
            raise ValueError(f"Unsupported sink database type: {database_type}")

        # Config is directly in sink, not nested under sink.config
        self.stream_sink_task = sink_class(
            dag=self.dag,
            node=self.node,
            execution_date=self.execution_date,
            variables=self.variables,
            config=sink_config,
        )

        # Parse transform SQL (optional)
        transform_config = node_config.get("transform", {})
        self.transform_sql = transform_config.get("sql", "").strip()
        if self.transform_sql:
            logger.info(f"Transform SQL configured: {self.transform_sql[:100]}...")
        else:
            logger.info("No transform SQL configured")

    @classmethod
    def to_dict(cls) -> dict:
        """Return operator metadata"""
        return {
            "name": cls.name(),
            "title": "Stream Operator",
            "description": "Real-time data streaming using Apache Flink CDC",
            "icon": "stream",
        }

    @classmethod
    def ui_config_schema(cls):
        """UI-specific config schema with connection-first approach"""
        return {
            "source": {
                "name": "Source",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "title": _l("Source Connection"),
                            "description": _l("Select database connection for CDC source"),
                            "ui:field": "ProjectConnectionSelectorField",
                            "ui:options": {
                                "supportTypes": ["postgres", "PostgreSQL", "mysql", "MySQL"],
                            },
                        },
                        "database_name": {
                            "type": "string",
                            "title": _l("Database Name"),
                            "description": _l("Database name for CDC source (leave empty to use connection default)"),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "plain",
                            },
                        },
                        "schema_name": {
                            "type": "string",
                            "title": _l("Schema Name"),
                            "description": _l(
                                "Schema name for CDC (leave empty to use project connection default schema)"
                            ),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "plain",
                            },
                        },
                        "table_name": {
                            "type": "string",
                            "title": _l("Table Name"),
                            "description": _l("Table name for CDC"),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "plain",
                            },
                        },
                    },
                    "required": ["connection_name", "table_name"],
                },
            },
            "sink": {
                "name": "Sink",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "title": _l("Sink Connection"),
                            "description": _l("Select database connection for sink"),
                            "ui:field": "ProjectConnectionSelectorField",
                            "ui:options": {
                                "supportTypes": [
                                    "postgres",
                                    "PostgreSQL",
                                    "mysql",
                                    "MySQL",
                                    "doris",
                                    "SelectDB(Doris)",
                                    "starrocks",
                                    "StarRocks",
                                    "kafka",
                                    "Kafka",
                                    "elasticsearch",
                                    "Elasticsearch",
                                    "clickhouse",
                                    "ClickHouse",
                                ],
                            },
                        },
                        "database_name": {
                            "type": "string",
                            "title": _l("Database Name"),
                            "description": _l("Target database name (leave empty to use connection default)"),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "plain",
                            },
                        },
                        "schema_name": {
                            "type": "string",
                            "title": _l("Schema Name"),
                            "description": _l(
                                "Target schema name (leave empty to use project connection default schema)"
                            ),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "plain",
                            },
                        },
                        "table_name": {
                            "type": "string",
                            "title": _l("Table Name"),
                            "description": _l("Target table name"),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "plain",
                            },
                        },
                    },
                    "required": ["connection_name", "table_name"],
                },
            },
            "transform": {
                "name": "Transform",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "unique_key": {
                            "type": "string",
                            "title": _l("Unique Key"),
                            "description": _l(
                                "Unique key for the sink table. Comma-separated list of columns.<br> For example: <b>id, name</b>"
                            ),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "plain",
                            },
                        },
                        "sql": {
                            "type": "string",
                            "title": _l("Transform SQL (Optional)"),
                            "description": _l(
                                "Optional SQL transformations for data processing. Example:<br>"
                                "SELECT * FROM <b>source_table_name</b> WHERE id > 100<br>"
                                "Use <b>source_table_name</b> as placeholder for the source table name."
                            ),
                            "ui:field": "CodeEditorWithReferencesField",
                            "ui:options": {
                                "type": "code",
                                "lang": "sql",
                            },
                        },
                    },
                    "required": ["unique_key"],
                },
            },
            "flink_config": {
                "name": "Flink Configuration",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "flink_connection_name": {
                            "type": "string",
                            "title": _l("Flink Connection"),
                            "description": _l(
                                "Flink cluster connection for job submission (filtered by stream engine flag)"
                            ),
                            "ui:field": "ProjectConnectionSelectorField",
                            "ui:options": {
                                "supportTypes": ["Apache Flink"],
                                # "disabled": True,
                            },
                        },
                        "parallelism": {
                            "type": "number",
                            "title": _l("Parallelism"),
                            "description": _l("Flink job parallelism (number of parallel tasks)"),
                            "default": DEFAULT_PARALLELISM,
                            "minimum": 1,
                            "maximum": 10,
                            "ui:options": {"controls": False},
                        },
                        "checkpoint_interval": {
                            "type": "number",
                            "title": _l("Checkpoint Interval (ms)"),
                            "description": _l("Checkpoint interval in milliseconds for fault tolerance"),
                            "default": CHECKPOINT_INTERVAL_DEFAULT,
                            "minimum": 1000,
                            "maximum": 60000,
                            "ui:options": {"controls": False},
                        },
                    },
                    "required": ["flink_connection_name"],
                },
            },
        }
