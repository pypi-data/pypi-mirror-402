"""MySQL CDC source task for Flink CDC streaming"""

import logging
from typing import TYPE_CHECKING

from recurvedata.exceptions import RecurveException
from recurvedata.executors.models import DataSource
from recurvedata.operators.stream_operator.const import SOURCE_TYPE_MYSQL
from recurvedata.operators.stream_operator.task import StreamSourceTask

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SourceConfig

logger = logging.getLogger(__name__)


class MySQLCDCSourceTask(StreamSourceTask):
    """
    MySQL CDC source using Flink CDC MySQL connector.

    Supports:
    - MySQL 5.7+
    - MySQL 8.0+
    - MariaDB 10.x
    - PolarDB MySQL
    - Aurora MySQL

    Features:
    - Incremental snapshot (no lock)
    - Parallel reading
    - Exactly-once semantics
    - Auto schema evolution

    Docs: https://nightlies.apache.org/flink/flink-cdc-docs-stable/docs/connectors/flink-sources/mysql-cdc/
    """

    ds_name_fields = ("connection_name",)
    worker_install_require = []  # No additional requirements, runs on Flink

    @staticmethod
    def build_cdc_config_by_datasource(datasource: DataSource, source_config: "SourceConfig") -> dict:
        database_name = source_config.database_name
        if not database_name:
            raise RecurveException(data="Database name must be configured in the project connection")

        table_name = source_config.table_name
        if not table_name:
            raise RecurveException(data="Table name must be configured in the project connection")

        cdc_config = {
            "connector": f"{SOURCE_TYPE_MYSQL}-cdc",
            "hostname": datasource.host,
            "port": datasource.port or 3306,
            "username": datasource.user,
            "password": datasource.password,
            "database-name": database_name,
            "table-name": table_name,
            "scan.startup.mode": "initial",
            "scan.incremental.snapshot.enabled": "false",  # TODO: support incremental snapshot
            # "scan.incremental.snapshot.chunk.key-column": "id",
        }
        return cdc_config

    @classmethod
    def config_schema(cls):
        """This schema is not used - StreamOperator provides its own ui_config_schema"""
        return {}
