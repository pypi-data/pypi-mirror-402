"""PostgreSQL sink task for Flink CDC streaming"""

import logging
from typing import TYPE_CHECKING

from recurvedata.exceptions import RecurveException
from recurvedata.executors.models import DataSource
from recurvedata.operators.stream_operator.task import StreamSinkTask

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SinkConfig

logger = logging.getLogger(__name__)


class PostgresSinkTask(StreamSinkTask):
    """
    PostgreSQL sink task for real-time data loading via JDBC.

    Supports:
    - PostgreSQL 9.6+, 10+, 11+, 12+, 13+, 14+, 15+, 16+

    Features:
    - JDBC-based streaming writes
    - Automatic table creation
    - Upsert support (INSERT ON CONFLICT)
    - Delete support

    Docs: https://nightlies.apache.org/flink/flink-cdc-docs-stable/docs/connectors/flink-sinks/jdbc/
    """

    ds_name_fields = ("connection_name",)
    worker_install_require = []

    @staticmethod
    def build_sink_config_by_datasource(datasource: DataSource, sink_config: "SinkConfig") -> dict:
        # Use database from config if provided, otherwise use connection's database
        database_name = datasource.database
        if not database_name:
            raise RecurveException(data="Database name must be configured in the project connection")

        table_name = sink_config.table_name
        if not table_name:
            raise RecurveException(data="Table name must be configured in the project connection")

        # Optional: Schema name
        if schema_name := sink_config.schema_name:
            table_name = f"{schema_name}.{table_name}"

        port = datasource.port or 5432

        sink_config = {
            "connector": "jdbc",
            "url": f"jdbc:postgresql://{datasource.host}:{port}/{database_name}",
            "username": datasource.user,
            "password": datasource.password,
            "table-name": table_name,
        }
        return sink_config

    @classmethod
    def config_schema(cls):
        """This schema is not used - StreamOperator provides its own ui_config_schema"""
        return {}
