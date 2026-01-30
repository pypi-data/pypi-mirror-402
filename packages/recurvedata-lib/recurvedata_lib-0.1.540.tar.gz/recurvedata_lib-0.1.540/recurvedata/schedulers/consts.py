import re
from enum import Enum


class OperatorEnum(str, Enum):
    SQLOperator = "SQLOperator"
    TransferOperator = "TransferOperator"
    PythonOperator = "PythonOperator"
    SparkOperator = "SparkOperator"
    NotifyOperator = "NotifyOperator"
    LinkOperator = "LinkOperator"


WORK_DIR = "/opt/airflow"  # todo: use /opt/recurve


class Operator(str, Enum):  # todo
    SQLOperator = "SQLOperator"
    TransferOperator = "TransferOperator"
    PythonOperator = "PythonOperator"
    SparkOperator = "SparkOperator"
    NotifyOperator = "NotifyOperator"
    LinkOperator = "LinkOperator"


class ScheduleType(str, Enum):
    crontab = "crontab"
    customization = "customization"  # 快捷设置
    manual = "manual"  # 手动触发


# All system DAGs must use this prefix, so they can be filtered out from task status sync
SYSTEM_DAG_PREFIX = "system_"
SYSTEM_SYNC_STATUS_DAG_ID = "system_sync_status"


def format_recurve_env_key(key: str) -> str:
    return f"RECURVE__{key.upper()}"


def get_dag_file_loc(job_id: int) -> str:
    # todo: configuration
    idx = job_id % 7
    return f"/opt/airflow/dags/autogen_sharding_{idx}.py"


DEFAULT_RETRY_NUMBER = 2
DEFAULT_RETRY_DELAY = 60 * 5  # 5 minutes


def is_dev_run_job(job_name: str) -> bool:
    pattern = r"dev_run_.*_\d+_\d+"
    match = re.match(pattern, job_name)
    return match is not None
