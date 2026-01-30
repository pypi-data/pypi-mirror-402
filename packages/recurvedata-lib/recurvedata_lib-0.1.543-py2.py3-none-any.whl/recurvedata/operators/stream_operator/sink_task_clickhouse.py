"""ClickHouse Sink Task for Stream Operator

ClickHouse sink using the community Flink connector.
Reference: https://github.com/itinycheng/flink-connector-clickhouse
"""

import logging
from typing import TYPE_CHECKING

from recurvedata.exceptions import RecurveException
from recurvedata.executors.models import DataSource
from recurvedata.operators.stream_operator.task import StreamSinkTask

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SinkConfig

logger = logging.getLogger(__name__)


class ClickHouseSinkTask(StreamSinkTask):
    """
    ClickHouse sink task for real-time data loading via JDBC.

    Supports:
    - ClickHouse 20.x, 21.x, 22.x, 23.x, 24.x

    Features:
    - JDBC-based streaming writes
    - Automatic table creation
    - Upsert support (ReplacingMergeTree)
    - High-performance batch inserts

    Supported ClickHouse engines:
    - MergeTree family (ReplacingMergeTree, SummingMergeTree, etc.)
    - Distributed tables
    - Local tables

    Note:
    - For upsert operations, use ReplacingMergeTree engine
    - Delete operations are not directly supported (use soft deletes)

    Docs: https://nightlies.apache.org/flink/flink-cdc-docs-stable/docs/connectors/flink-sinks/jdbc/
    """

    ds_name_fields = ("connection_name",)
    worker_install_require = []

    @staticmethod
    def build_sink_config_by_datasource(datasource: DataSource, sink_config: "SinkConfig") -> dict:
        # Use database from config if provided, otherwise use connection's database
        database_name = sink_config.database_name or datasource.database
        if not database_name:
            raise RecurveException(data="Database name must be configured in the project connection")

        table_name = sink_config.table_name
        if not table_name:
            raise RecurveException(data="Table name must be configured in the project connection")

        # ClickHouse default HTTP port is 8123, but JDBC typically uses native port 9000
        # However, the clickhouse-jdbc driver can use HTTP port with proper URL
        http_port = 8123  # allow to configure in the future

        sink_config = {
            "connector": "clickhouse",
            "url": f"jdbc:ch://{datasource.host}:{http_port}",
            "database-name": database_name,
            "table-name": table_name,
            "username": datasource.user,
            "password": datasource.password,
        }
        return sink_config

    @classmethod
    def config_schema(cls):
        """This schema is not used - StreamOperator provides its own ui_config_schema"""
        return {}
