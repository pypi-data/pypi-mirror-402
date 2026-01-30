import datetime
import os

from airflow.models import DAG
from airflow.timetables.interval import CronDataIntervalTimetable

from recurvedata.schedulers.airflow import AirflowScheduler
from recurvedata.schedulers.model import SchedulerNode
from recurvedata.schedulers.utils import format_dag_id


def prepare_airflow_env():
    if "_AIRFLOW__AS_LIBRARY" in os.environ:
        del os.environ["_AIRFLOW__AS_LIBRARY"]


def get_dag_from_db(dag_id):
    from airflow.exceptions import AirflowException
    from airflow.models import DagBag

    dagbag = DagBag(read_dags_from_db=True)
    dag = dagbag.get_dag(dag_id)
    if not dag:
        raise AirflowException(f"Dag {dag_id!r} could not be found; either it does not exist or it failed to parse.")
    return dag


def build_execute_context(dag, task, run_id) -> dict:
    dag_run = dag.get_dagrun(run_id=run_id)
    task_instance = dag_run.get_task_instance(task.task_id)
    context = {
        "dag": dag,
        "task": task,
        "dag_run": dag_run,
        "task_instance": task_instance,
        "execution_date": dag_run.execution_date,
        "logical_date": dag_run.logical_date,
        "data_interval_end": dag_run.data_interval_end,
    }

    return context


def format_external_dag_id(job_id: int) -> str:
    return format_dag_id(job_id)


def format_external_task_id(node_key: str) -> str:
    node = SchedulerNode(node_key=node_key, operator="external_operator", id=0, name="external_task")
    return AirflowScheduler.format_task_id(node)


def data_interval_end_to_data_interval_start(
    dag: DAG, data_interval_end: datetime.datetime
) -> datetime.datetime | None:
    if hasattr(dag, "timetable") and isinstance(dag.timetable, CronDataIntervalTimetable):
        data_interval_start = dag.timetable._get_prev(data_interval_end)
        data_interval_end2 = dag.timetable._get_next(data_interval_start)
        if data_interval_end2 != data_interval_end:
            data_interval_start = dag.timetable._get_prev(data_interval_start)
        return data_interval_start
    else:
        return data_interval_end
