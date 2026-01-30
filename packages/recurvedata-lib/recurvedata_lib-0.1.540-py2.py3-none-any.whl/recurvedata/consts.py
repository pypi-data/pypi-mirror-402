from enum import Enum

# docker container environ key for recurve environment_id
ENV_ID_KEY = "RECURVE__ENVIRONMENT_ID"
PROJECT_ID_KEY = "RECURVE__PROJECT_ID"


class ScheduleType(str, Enum):
    crontab = "crontab"
    customization = "customization"
    manual = "manual"


class Operator(str, Enum):
    SQLOperator = "SQLOperator"
    TransferOperator = "TransferOperator"
    StreamOperator = "StreamOperator"
    PythonOperator = "PythonOperator"
    SparkOperator = "SparkOperator"
    NotifyOperator = "NotifyOperator"
    LinkOperator = "LinkOperator"
    DBTOperator = "DBTOperator"
    LinkModelPipelineOperator = "LinkModelPipelineOperator"
    SensorOperator = "SensorOperator"

    @classmethod
    def is_link(cls, op: str):
        return op in (cls.LinkOperator, cls.LinkModelPipelineOperator)

    # todo(chenjingmeng): support dynamically added Operator


class ETLExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


class ConnectionCategory(str, Enum):
    DATABASE = "database"
    STORAGE = "storage"
    WAREHOUSE = "warehouse"
    OTHERS = "others"
    SERVICE = "service"
    BI = "bi"


class ConnectorGroup(str, Enum):
    SOURCE = "source"
    DESTINATION = "destination"
    INTEGRATION = "integration"
