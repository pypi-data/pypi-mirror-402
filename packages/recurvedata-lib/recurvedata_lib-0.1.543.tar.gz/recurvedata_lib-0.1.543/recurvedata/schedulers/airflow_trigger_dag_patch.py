"""
monkey patch airflow airflow/api/common/trigger_dag.py,
airflow native _trigger_dag will create data_interval_end = execution_date dag run,
which will cause plan run error (one data_interval_end may have multiple run_id).
"""

import json
import logging
from datetime import datetime

import airflow.api.common.trigger_dag
from airflow.exceptions import DagNotFound, DagRunAlreadyExists
from airflow.models import DagBag, DagRun
from airflow.models.dag import DAG
from airflow.timetables.base import DataInterval
from airflow.timetables.interval import CronDataIntervalTimetable
from airflow.utils import timezone
from airflow.utils.state import DagRunState
from airflow.utils.types import DagRunType

logger = logging.getLogger(__name__)


def _recurve_get_next_data_interval(mannual_data_interval: DataInterval, dag: DAG):
    if not isinstance(dag.timetable, CronDataIntervalTimetable):
        return mannual_data_interval
    next_data_interval_end = dag.timetable._get_next(mannual_data_interval.end)
    return DataInterval(start=mannual_data_interval.end, end=next_data_interval_end)


def _recurve_trigger_dag(
    dag_id: str,
    dag_bag: DagBag,
    run_id: str | None = None,
    conf: dict | str | None = None,
    execution_date: datetime | None = None,
    replace_microseconds: bool = True,
) -> list[DagRun | None]:
    """
    Triggers DAG run.

    :param dag_id: DAG ID
    :param dag_bag: DAG Bag model
    :param run_id: ID of the dag_run
    :param conf: configuration
    :param execution_date: date of execution
    :param replace_microseconds: whether microseconds should be zeroed
    :return: list of triggered dags
    """
    logger.info("start call _recurve_trigger_dag")
    dag = dag_bag.get_dag(dag_id)  # prefetch dag if it is stored serialized

    if dag is None or dag_id not in dag_bag.dags:
        raise DagNotFound(f"Dag id {dag_id} not found")

    execution_date = execution_date or timezone.utcnow()

    if not timezone.is_localized(execution_date):
        raise ValueError("The execution_date should be localized")

    if replace_microseconds:
        execution_date = execution_date.replace(microsecond=0)

    if dag.default_args and "start_date" in dag.default_args:
        min_dag_start_date = dag.default_args["start_date"]
        if min_dag_start_date and execution_date < min_dag_start_date:
            raise ValueError(
                f"The execution_date [{execution_date.isoformat()}] should be >= start_date "
                f"[{min_dag_start_date.isoformat()}] from DAG's default_args"
            )
    logical_date = timezone.coerce_datetime(execution_date)

    data_interval = dag.timetable.infer_manual_data_interval(run_after=logical_date)

    # recurve update start #
    recurve_external_trigger = True
    inferred_run_type = DagRunType.from_run_id(run_id)
    if inferred_run_type == DagRunType.SCHEDULED:
        new_data_interval = _recurve_get_next_data_interval(data_interval, dag)
        logger.info(f"adjust data interval: {data_interval} -> {new_data_interval}")
        data_interval = new_data_interval
        recurve_external_trigger = False
    # recurve update end #

    run_id = run_id or dag.timetable.generate_run_id(
        run_type=DagRunType.MANUAL, logical_date=logical_date, data_interval=data_interval
    )
    dag_run = DagRun.find_duplicate(dag_id=dag_id, execution_date=execution_date, run_id=run_id)

    if dag_run:
        raise DagRunAlreadyExists(dag_run=dag_run, execution_date=execution_date, run_id=run_id)

    run_conf = None
    if conf:
        run_conf = conf if isinstance(conf, dict) else json.loads(conf)

    # recurve update start #
    dag_runs = []
    dags_to_run = [dag, *dag.subdags]
    for _dag in dags_to_run:
        dag_run = _dag.create_dagrun(
            run_id=run_id,
            execution_date=execution_date,
            state=DagRunState.QUEUED,
            conf=run_conf,
            external_trigger=recurve_external_trigger,
            dag_hash=dag_bag.dags_hash.get(dag_id),
            data_interval=data_interval,
        )
        dag_runs.append(dag_run)
    # recurve update end #

    return dag_runs


logger.info("monkey patch airflow.api.common.trigger_dag._trigger_dag")
airflow.api.common.trigger_dag._trigger_dag = _recurve_trigger_dag
