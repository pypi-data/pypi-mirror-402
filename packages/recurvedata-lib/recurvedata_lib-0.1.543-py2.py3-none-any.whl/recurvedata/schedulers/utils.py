import datetime
import json
import logging
from typing import Generator

from airflow.models import DAG, BaseOperator
from airflow.utils.session import create_session
from slugify import slugify

from recurvedata.schedulers.client import SchedulerClient

logger = logging.getLogger(__name__)


def get_tasks(dag: DAG, recurve_node_key: str = None) -> Generator[BaseOperator, None, None]:
    if recurve_node_key:
        for task in dag.task_dict.values():
            if task.doc_json and json.loads(task.doc_json).get("recurve_node_key") == recurve_node_key:
                yield task


def clear_task_instance(
    dag: DAG,
    recurve_node_key: str,
    execution_date: datetime.datetime,
    only_failed: bool = False,
    including_downstream: bool = False,
):
    clear_task_ids: list[str] = []
    for task in get_tasks(dag, recurve_node_key):
        clear_task_ids.append(task.task_id)
    airflow_execution_date = dag.previous_schedule(execution_date)  # todo: timezone
    with create_session() as session:
        dag = dag.partial_subset(task_ids_or_regex=clear_task_ids, include_downstream=including_downstream)
        clear_task_ids = [tid for tid in dag.task_dict]
        logger.info(f"prepare to clear dag: {dag.dag_id}, {clear_task_ids} execution_date: {airflow_execution_date}")

        clear_cnt = dag.clear(
            task_ids=clear_task_ids,
            start_date=airflow_execution_date,
            end_date=airflow_execution_date,
            only_failed=only_failed,
            session=session,
        )
        logger.info(
            f"finish clear dag: {dag.dag_id}, {clear_task_ids} execution_date: {airflow_execution_date}, total clear: {clear_cnt} task_instances"
        )


def slugify_text(s: str) -> str:
    """A simple wrapper to python-slugify, using custom regex_pattern to keep `.` and `_` as is

    >>> slugify_text('我是谁')
    'wo-shi-shui'
    >>> slugify_text('load_fact_user_stats')
    'load_fact_user_stats'
    >>> slugify_text('tidb prepare category tables')
    'tidb-prepare-category-tables'
    >>> slugify_text('estimate daily deal 2017.10.20')
    'estimate-daily-deal-2017.10.20'
    """
    return slugify(s, regex_pattern=r"[^-a-zA-Z0-9\._]+")


def format_dag_id(job_id: int) -> str:
    """
    please do not adjust this function
    """
    return str(job_id)


def init_client() -> SchedulerClient:
    return SchedulerClient()
