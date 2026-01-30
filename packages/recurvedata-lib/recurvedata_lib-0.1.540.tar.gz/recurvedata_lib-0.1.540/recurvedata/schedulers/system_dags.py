import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

from recurvedata.schedulers.consts import SYSTEM_SYNC_STATUS_DAG_ID


def create_system_dags():
    """
    Create all system DAGs.

    IMPORTANT: All system DAG IDs must start with SYSTEM_DAG_PREFIX ('system_').
    This ensures they are filtered out from task status sync in TaskStatusScanner.
    """
    return [
        create_sync_status_dag(),
        create_cleanup_logs_and_meta_dag(),
    ]


def _prepare_bash_env():
    dct = {}
    for key, val in os.environ.items():
        if key.startswith("RECURVE__"):
            dct[key] = val
        elif key.startswith("AIRFLOW"):
            dct[key] = val
        elif key in (
            "PATH",
            "PYENV_ROOT",
        ):
            dct[key] = os.environ[key]
    return dct


def create_sync_status_dag():
    start_date = datetime(2024, 8, 5)
    default_args = {
        "depends_on_past": False,
        "retries": 150,
        "retry_delay": timedelta(seconds=10),
        "priority_weight": 100,
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(seconds=30),
    }
    dag = DAG(
        SYSTEM_SYNC_STATUS_DAG_ID,
        default_args=default_args,
        description="A DAG to sync db status",
        schedule_interval="0 */6 * * *",  # Run every 6 hours
        start_date=start_date,
        catchup=False,
        dagrun_timeout=timedelta(minutes=60 * 6),
        max_active_runs=1,  # todo: retry may delay the future dag_run
        is_paused_upon_creation=False,
    )

    BashOperator(
        task_id="sync_status",
        bash_command="recurve_scheduler sync-task-status --interval=5",
        dag=dag,
        env=_prepare_bash_env(),
    )
    return dag


def create_cleanup_logs_and_meta_dag():
    """
    System maintenance DAG:
    - Clean old Airflow task logs under /opt/airflow/logs
    - Clean old executor meta files under /opt/recurve/meta
    """
    start_date = datetime(2024, 1, 1)
    default_args = {
        "depends_on_past": False,
        "retries": 2,
        "priority_weight": 10,
    }

    dag = DAG(
        dag_id="system_cleanup_logs_and_meta",
        default_args=default_args,
        description="Clean old Airflow logs and executor meta files",
        schedule_interval="0 3 * * *",  # Daily at 3 AM
        start_date=start_date,
        catchup=False,
        dagrun_timeout=timedelta(minutes=60),
        max_active_runs=1,
        is_paused_upon_creation=False,
    )

    BashOperator(
        task_id="delete_old_logs_and_meta",
        bash_command="""
set -e

RETENTION_DAYS={{ var.value.get('log_retention_days', '14') }}

echo "Cleaning Airflow logs older than ${RETENTION_DAYS} days..."
find /opt/airflow/logs -type f -mtime +${RETENTION_DAYS} -delete || true
find /opt/airflow/logs -type d -empty -delete || true

echo "Cleaning Recurve executor meta older than ${RETENTION_DAYS} days..."
find /opt/recurve/meta -type f -mtime +${RETENTION_DAYS} -delete || true
find /opt/recurve/meta -type d -empty -delete || true

echo "Cleanup finished."
""",
        dag=dag,
        env=_prepare_bash_env(),
    )

    return dag
