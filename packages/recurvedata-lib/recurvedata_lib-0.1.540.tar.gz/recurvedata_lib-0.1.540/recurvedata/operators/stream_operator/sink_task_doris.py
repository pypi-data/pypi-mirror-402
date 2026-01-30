"""Apache Doris sink task for Flink CDC streaming"""

import logging
from typing import TYPE_CHECKING

from recurvedata.exceptions import RecurveException
from recurvedata.executors.models import DataSource
from recurvedata.operators.stream_operator.const import SINK_TYPE_DORIS
from recurvedata.operators.stream_operator.task import StreamSinkTask

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SinkConfig

logger = logging.getLogger(__name__)


class DorisSinkTask(StreamSinkTask):
    """
    Apache Doris sink task for real-time data loading.

    Supports:
    - Apache Doris 1.2+, 2.x
    - SelectDB (Doris-based)

    Features:
    - Stream load for real-time ingestion
    - Two-phase commit (2PC) for exactly-once
    - Auto table creation
    - Schema evolution
    - Delete support

    Docs: https://nightlies.apache.org/flink/flink-cdc-docs-release-3.5/docs/connectors/pipeline-connectors/doris/
    """

    ds_name_fields = ("connection_name",)
    worker_install_require = []

    @staticmethod
    def build_sink_config_by_datasource(datasource: DataSource, sink_config: "SinkConfig") -> dict:
        """Build Doris sink configuration from a DataSource object.

        Args:
            datasource: DataSource object containing connection details
            sink_config: SinkConfig object containing sink table information

        Returns:
            dict: Doris sink configuration for Flink CDC YAML

        Raises:
            RecurveException: If required fields are missing
        """
        # Validate required fields
        database_name = datasource.database
        if not database_name:
            raise RecurveException(data="Database name must be configured in the project connection")

        table_name = sink_config.table_name
        if not table_name:
            raise RecurveException(data="Table name must be configured in the sink config")

        # Use Doris default ports
        fe_http_port = datasource.data.get("http_port") or 8030

        # Build Doris sink configuration
        sink_config_dict = {
            "connector": SINK_TYPE_DORIS,
            "fenodes": f"{datasource.host}:{fe_http_port}",
            "username": datasource.user,
            "password": datasource.password or "",
            "table.identifier": f"{database_name}.{table_name}",
            "sink.label-prefix": "reorc",
            "sink.properties.format": "json",
            "sink.properties.read_json_by_line": "true",
            "sink.enable-2pc": True,
            "sink.enable-delete": True,
        }

        return sink_config_dict

    @classmethod
    def config_schema(cls):
        return {}
