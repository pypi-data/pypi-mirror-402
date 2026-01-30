# Stream Operator Constants

# CDC formats
CDC_FORMAT_DEBEZIUM = "DEBEZIUM"  # Debezium JSON format

# Checkpoint intervals (milliseconds)
CHECKPOINT_INTERVAL_DEFAULT = 3000  # 3 seconds
# Pipeline defaults
DEFAULT_PARALLELISM = 1

# Source types
SOURCE_TYPE_MYSQL = "mysql"
SOURCE_TYPE_POSTGRES = "postgres"

# Sink types
SINK_TYPE_DORIS = "doris"
SINK_TYPE_STARROCKS = "starrocks"
SINK_TYPE_KAFKA = "kafka"
SINK_TYPE_ELASTICSEARCH = "elasticsearch"
SINK_TYPE_CLICKHOUSE = "clickhouse"
SINK_TYPE_POSTGRES = "postgres"
SINK_TYPE_MYSQL = "mysql"

# Lists for UI display
STREAM_SOURCE_TYPES = [
    SOURCE_TYPE_MYSQL,
    SOURCE_TYPE_POSTGRES,
]

STREAM_SINK_TYPES = [
    SINK_TYPE_DORIS,
    SINK_TYPE_STARROCKS,
    SINK_TYPE_KAFKA,
    SINK_TYPE_ELASTICSEARCH,
    SINK_TYPE_CLICKHOUSE,
    SINK_TYPE_POSTGRES,
    SINK_TYPE_MYSQL,
]

# Supported source-sink combinations
# ClickHouse sink uses community connector: https://github.com/itinycheng/flink-connector-clickhouse
SUPPORTED_COMBINATIONS = {
    SOURCE_TYPE_MYSQL: [
        SINK_TYPE_DORIS,
        SINK_TYPE_STARROCKS,
        SINK_TYPE_KAFKA,
        SINK_TYPE_ELASTICSEARCH,
        SINK_TYPE_CLICKHOUSE,
        SINK_TYPE_POSTGRES,
        SINK_TYPE_MYSQL,
    ],
    SOURCE_TYPE_POSTGRES: [
        SINK_TYPE_DORIS,
        SINK_TYPE_STARROCKS,
        SINK_TYPE_KAFKA,
        SINK_TYPE_ELASTICSEARCH,
        SINK_TYPE_CLICKHOUSE,
        SINK_TYPE_POSTGRES,
        SINK_TYPE_MYSQL,
    ],
}
