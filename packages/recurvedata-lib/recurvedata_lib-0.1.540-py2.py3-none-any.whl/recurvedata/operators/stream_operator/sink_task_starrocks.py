"""StarRocks sink task for Flink CDC streaming"""

import logging
from typing import TYPE_CHECKING

from recurvedata.exceptions import RecurveException
from recurvedata.executors.models import DataSource
from recurvedata.operators.stream_operator.const import SINK_TYPE_STARROCKS
from recurvedata.operators.stream_operator.task import StreamSinkTask

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SinkConfig

logger = logging.getLogger(__name__)


class StarRocksSinkTask(StreamSinkTask):
    """
    StarRocks sink task for real-time data loading.

    Supports:
    - StarRocks 2.x, 3.x
    - CelerData (StarRocks-based)

    Features:
    - Stream load for real-time ingestion
    - Two-phase commit (2PC) for exactly-once
    - Auto table creation
    - Schema evolution
    - Delete support

    Docs: https://nightlies.apache.org/flink/flink-cdc-docs-release-3.5/docs/connectors/pipeline-connectors/starrocks/
    """

    ds_name_fields = ("connection_name",)
    worker_install_require = []

    @staticmethod
    def build_sink_config_by_datasource(datasource: DataSource, sink_config: "SinkConfig") -> dict:
        """Build StarRocks sink configuration from a DataSource object.

        Args:
            datasource: DataSource object containing connection details
            sink_config: SinkConfig object containing sink table information

        Returns:
            dict: StarRocks sink configuration for Flink CDC YAML

        Raises:
            RecurveException: If required fields are missing
        """
        # Validate required fields
        database_name = sink_config.database_name or datasource.database
        if not database_name:
            raise RecurveException(data="Database name must be configured in the project connection")

        table_name = sink_config.table_name
        if not table_name:
            raise RecurveException(data="Table name must be configured in the sink config")

        # Use StarRocks default ports
        # FE HTTP port for stream load (default 8030)
        fe_http_port = datasource.data.get("http_port") or 8030
        port = datasource.data.get("port") or 9030

        # Build StarRocks sink configuration
        sink_config_dict = {
            "connector": SINK_TYPE_STARROCKS,
            "load-url": f"{datasource.host}:{fe_http_port}",
            "jdbc-url": f"jdbc:mysql://{datasource.host}:{port}",
            "username": datasource.user,
            "password": datasource.password or "",
            "database-name": database_name,
            "table-name": table_name,
            "sink.label-prefix": "reorc",
            "sink.properties.format": "json",
            "sink.properties.strip_outer_array": "true",
            # Use at-least-once semantic (no version check required)
            "sink.semantic": "at-least-once",
            # Disable 2PC which requires version detection
            "sink.at-least-once.use-transaction-stream-load": "false",
        }

        return sink_config_dict

    @classmethod
    def config_schema(cls):
        """This schema is not used - StreamOperator provides its own ui_config_schema"""
        return {}
