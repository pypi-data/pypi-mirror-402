import logging
import os

from airflow.providers.celery.executors.celery_executor import app as celery_app
from celery import Task

from recurvedata.executors.client import ExecutorClient
from recurvedata.operators.config import CONF
from recurvedata.utils.mp import run_subprocess

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def debug_node(
    self: Task,
    workflow_id: int,
    node_key: str,
    schedule_type: str,
    schedule_interval: str,
    execution_date: str,
    timezone: str,
):
    task_id = self.request.id
    logging.info(
        f"start {task_id} {workflow_id} {node_key} {schedule_type} {schedule_interval} {execution_date} {timezone}"
    )

    executor_client = ExecutorClient()

    executor_client.debug_start(workflow_id, node_key, task_id)
    try:
        run_subprocess(
            [
                os.path.join(CONF.RECURVE_EXECUTOR_PYENV_BIN_PATH, "recurve_executor"),
                "debug",
                "--workflow_id",
                f"{workflow_id}",
                "--node_key",
                f"{node_key}",
                "--schedule_type",
                schedule_type,
                "--schedule_interval",
                schedule_interval,
                "--execution_date",
                execution_date,
                "--timezone",
                timezone,
                "--celery_task_id",
                task_id,
            ],
            env=os.environ.copy(),
        )
        is_success = True
    except Exception as e:
        logger.exception(f"{workflow_id} {node_key} {execution_date} debug failed, err: {e}")
        is_success = False
    executor_client.debug_end(workflow_id, node_key, task_id, is_success)


def revoke_task(task_id: str = None, terminate=True):
    return celery_app.control.revoke(task_id, terminate=terminate)
