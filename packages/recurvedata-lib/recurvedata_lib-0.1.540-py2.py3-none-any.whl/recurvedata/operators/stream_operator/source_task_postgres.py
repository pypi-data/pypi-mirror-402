"""PostgreSQL CDC source task for Flink CDC streaming"""

import logging
from typing import TYPE_CHECKING

from recurvedata.exceptions import RecurveException
from recurvedata.executors.models import DataSource
from recurvedata.operators.stream_operator.const import SOURCE_TYPE_POSTGRES
from recurvedata.operators.stream_operator.task import StreamSourceTask

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SourceConfig

logger = logging.getLogger(__name__)


class PostgresCDCSourceTask(StreamSourceTask):
    """
    PostgreSQL CDC source using Flink CDC PostgreSQL connector.

    Supports:
    - PostgreSQL 9.6+
    - PostgreSQL 10+, 11+, 12+, 13+, 14+, 15+, 16+

    Requirements:
    - WAL level = logical (configured automatically)
    - Replication slot (auto-generated based on database/schema/table)
    - pgoutput plugin (built-in)

    Features:
    - Incremental snapshot
    - Parallel reading
    - Exactly-once semantics
    - Schema evolution support
    - Automatic replication slot management

    Docs: https://nightlies.apache.org/flink/flink-cdc-docs-stable/docs/connectors/flink-sources/postgres-cdc/
    """

    ds_name_fields = ("connection_name",)
    worker_install_require = []

    @staticmethod
    def build_cdc_config_by_datasource(datasource: DataSource, source_config: "SourceConfig") -> dict:
        database_name = source_config.database_name
        if not database_name:
            raise RecurveException(data="Database name must be configured in the project connection")
        schema_name = source_config.schema_name or "public"
        table_name = source_config.table_name
        if not table_name:
            raise RecurveException(data="Table name must be configured in the project connection")
        slot_name = source_config.slot_name
        if not slot_name:
            raise RecurveException(data="Slot name must be configured in the project connection")

        cdc_config = {
            "connector": f"{SOURCE_TYPE_POSTGRES}-cdc",
            "hostname": datasource.host,
            "port": datasource.port or 5432,
            "username": datasource.user,
            "password": datasource.password,
            "database-name": database_name,
            "schema-name": schema_name,
            "table-name": table_name,
            "slot.name": slot_name,
            "debezium.slot.drop.on.stop": "true",
            "decoding.plugin.name": "pgoutput",
            "scan.startup.mode": "initial",  # Always use initial mode (snapshot + WAL)
        }
        return cdc_config

    @classmethod
    def config_schema(cls):
        """This schema is not used - StreamOperator provides its own ui_config_schema"""
        return {}
