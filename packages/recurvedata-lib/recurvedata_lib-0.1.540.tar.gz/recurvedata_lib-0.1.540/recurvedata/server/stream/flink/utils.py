from typing import TYPE_CHECKING

from loguru import logger

from recurvedata.exceptions import RecurveException
from recurvedata.executors.models import DataSource
from recurvedata.operators.stream_operator.const import (
    SINK_TYPE_CLICKHOUSE,
    SINK_TYPE_DORIS,
    SINK_TYPE_MYSQL,
    SINK_TYPE_POSTGRES,
    SINK_TYPE_STARROCKS,
    SOURCE_TYPE_MYSQL,
    SOURCE_TYPE_POSTGRES,
)

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SinkConfig, SourceConfig


def build_cdc_config_by_datasource(datasource: DataSource, source_config: "SourceConfig") -> dict:
    """
    Move this to Operators > Stream Operator > Task.py
    """
    # Lazy imports to avoid circular dependency
    from recurvedata.operators.stream_operator.source_task_mysql import MySQLCDCSourceTask
    from recurvedata.operators.stream_operator.source_task_postgres import PostgresCDCSourceTask

    if datasource.ds_type == SOURCE_TYPE_POSTGRES:
        return PostgresCDCSourceTask.build_cdc_config_by_datasource(datasource, source_config)
    if datasource.ds_type == SOURCE_TYPE_MYSQL:
        return MySQLCDCSourceTask.build_cdc_config_by_datasource(datasource, source_config)
    raise RecurveException(data=f"Unsupported datasource type: {datasource.ds_type}")


def build_sink_config_by_datasource(datasource: DataSource, sink_config: "SinkConfig") -> dict:
    # Lazy imports to avoid circular dependency
    from recurvedata.operators.stream_operator.sink_task_clickhouse import ClickHouseSinkTask
    from recurvedata.operators.stream_operator.sink_task_doris import DorisSinkTask
    from recurvedata.operators.stream_operator.sink_task_mysql import MySQLSinkTask
    from recurvedata.operators.stream_operator.sink_task_postgres import PostgresSinkTask
    from recurvedata.operators.stream_operator.sink_task_starrocks import StarRocksSinkTask

    if datasource.ds_type == SINK_TYPE_POSTGRES:
        return PostgresSinkTask.build_sink_config_by_datasource(datasource, sink_config)
    if datasource.ds_type == SINK_TYPE_MYSQL:
        return MySQLSinkTask.build_sink_config_by_datasource(datasource, sink_config)
    if datasource.ds_type == SINK_TYPE_DORIS:
        return DorisSinkTask.build_sink_config_by_datasource(datasource, sink_config)
    if datasource.ds_type == SINK_TYPE_CLICKHOUSE:
        return ClickHouseSinkTask.build_sink_config_by_datasource(datasource, sink_config)
    if datasource.ds_type == SINK_TYPE_STARROCKS:
        return StarRocksSinkTask.build_sink_config_by_datasource(datasource, sink_config)
    raise RecurveException(data=f"Unsupported datasource type: {datasource.ds_type}")


def convert_column_type_to_flink_type(normalized_type: str) -> str:
    """
    Convert a normalized column type to its corresponding Flink SQL data type.

    Args:
        normalized_type: The normalized type string (e.g., 'integer', 'string', 'datetime')

    Returns:
        The corresponding Flink SQL data type
    """
    # Mapping from normalized types to Flink data types
    NORMALIZED_TO_FLINK_TYPE = {
        "integer": "INT",  # Use INT for integer
        "float": "DOUBLE",  # DOUBLE for floating point numbers
        "string": "STRING",  # STRING for text data
        "boolean": "BOOLEAN",  # BOOLEAN for true/false values
        "date": "DATE",  # DATE for date-only values
        "datetime": "TIMESTAMP",  # TIMESTAMP for datetime values
        "time": "TIME",  # TIME for time-only values
        "binary": "BYTES",  # BYTES for binary data
        "json": "STRING",  # JSON as STRING in Flink (Flink doesn't have native JSON type)
    }

    normalized_type_lower = normalized_type.lower().strip()

    if normalized_type_lower not in NORMALIZED_TO_FLINK_TYPE:
        logger.warning(f"Unsupported normalized type: {normalized_type_lower}, using STRING as default")
        return "STRING"

    return NORMALIZED_TO_FLINK_TYPE[normalized_type_lower]
