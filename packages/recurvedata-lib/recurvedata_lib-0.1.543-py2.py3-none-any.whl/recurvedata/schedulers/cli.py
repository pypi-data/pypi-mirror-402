import json
import logging
from typing import Any

import dateutil
import typer
from airflow.models import DAG
from airflow.utils.state import TaskInstanceState

from recurvedata.schedulers.airflow_db_process import AirflowDbService
from recurvedata.schedulers.schemas import BundleTask, WorkflowNodeDebugDetail
from recurvedata.schedulers.service import get_job_dag
from recurvedata.schedulers.task_status import TaskStatusScanner
from recurvedata.schedulers.utils import clear_task_instance, format_dag_id, init_client
from recurvedata.utils import init_logging
from recurvedata.utils._typer import RecurveTyper
from recurvedata.utils.date_time import to_local_datetime

logger = logging.getLogger(__name__)
cli = RecurveTyper()


def _ensure_dag_exists(job_id: int, raise_error=True) -> DAG | None:
    dag = get_job_dag(job_id)
    if not dag:  # job deleted
        if not raise_error:
            logger.info(f"dag missing for job {job_id}")
            return
        raise ValueError(f"dag not exists: {job_id}")
    return dag


@cli.callback()
def init():
    init_logging()


@cli.command()
def update_dag(job_id: int = typer.Option(..., "--job_id")):
    dag = _ensure_dag_exists(job_id, raise_error=False)
    AirflowDbService.update_dag(dag)


@cli.command()
def activate_dag(job_id: int = typer.Option(..., "--job_id")):
    dag = _ensure_dag_exists(job_id, raise_error=False)
    AirflowDbService.activate_dag(dag)


@cli.command()
def deactivate_dag(job_id: int = typer.Option(..., "--job_id")):
    dag = _ensure_dag_exists(job_id, raise_error=False)
    AirflowDbService.deactivate_dag(dag)


@cli.command()
def delete_dag(job_id: int = typer.Option(..., "--job_id"), job_name: str = typer.Option(..., "--job_name")):
    dag_id = format_dag_id(job_id)
    AirflowDbService.delete_dag(dag_id, job_name)


@cli.command()
def clear(
    job_id: int = typer.Option(..., "--job_id"),
    node_key: str = typer.Option(..., "--node_key"),
    execution_date: str = typer.Option(..., "--execution_date", callback=to_local_datetime),
    only_failed: bool = typer.Option(False, "--only_failed"),
    including_downstream: bool = typer.Option(False, "--including_downstream"),
):
    dag = get_job_dag(job_id)
    clear_task_instance(dag, node_key, execution_date, only_failed, including_downstream)


@cli.command()
def start_workflow_node_debug(
    workflow_id: int = typer.Option(..., "--workflow_id"),
    node_key: str = typer.Option(..., "--node_key"),
    schedule_type: str = typer.Option(..., "--schedule_type"),
    schedule_interval: str = typer.Option(..., "--schedule_interval"),
    execution_date: str = typer.Option(..., "--execution_date"),
    timezone: str = typer.Option(..., "--timezone"),
):
    from celery.result import AsyncResult

    from recurvedata.schedulers.debug_celery import debug_node

    celery_kwargs = {
        "workflow_id": workflow_id,
        "node_key": node_key,
        "schedule_type": schedule_type,
        "schedule_interval": schedule_interval,
        "execution_date": execution_date,
        "timezone": timezone,
    }
    result: AsyncResult = debug_node.apply_async(kwargs=celery_kwargs)
    logger.info(f"sent debug_node {celery_kwargs}, celery_id: {result.task_id}")
    return {
        "celery_task_id": result.task_id,
    }


@cli.command()
def abort_workflow_node_debug(
    workflow_id: int = typer.Option(..., "--workflow_id"),
    node_key: str = typer.Option(..., "--node_key"),
    celery_task_id: str = typer.Option(None, "--celery_task_id"),
):
    import recurvedata.schedulers.debug_celery

    if not celery_task_id:
        client = init_client()
        detail: WorkflowNodeDebugDetail = client.get_workflow_node_debug_detail(
            workflow_id=workflow_id, node_key=node_key
        )
        celery_task_id = detail.celery_task_id

    if not celery_task_id:
        logger.info("skip revoke_debug, no celery_task_id found")
        return
    logger.info(f"start revoke debug: {workflow_id} {node_key} {celery_task_id}")
    recurvedata.schedulers.debug_celery.revoke_task(celery_task_id)
    logger.info(f"finish revoke debug: {workflow_id} {node_key} {celery_task_id}")


@cli.command()
def sync_task_status(interval: int = typer.Option(5, "--interval")):
    scanner = TaskStatusScanner()
    scanner.run(interval)


@cli.command()
def trigger_job_run(
    job_id: int = typer.Option(..., "--job_id"),
    execution_date: str = typer.Option(..., "--execution_date", callback=to_local_datetime),
    include_past: bool = typer.Option(False, "--include_past"),
    include_future: bool = typer.Option(False, "--include_future"),
    run_type: str = typer.Option(None, "--run_type"),
    conf: str = typer.Option(None, "--conf"),
):
    dag = _ensure_dag_exists(job_id)
    if conf:
        conf: dict[str, Any] = json.loads(conf)
    AirflowDbService.trigger_job_run(dag, execution_date, include_past, include_future, run_type, conf)


@cli.command()
def rerun_job_run(
    job_id: int = typer.Option(..., "--job_id"),
    run_id: str = typer.Option(None, "--run_id"),
    min_execution_date: str = typer.Option(None, "--min_execution_date"),
    max_execution_date: str = typer.Option(None, "--max_execution_date"),
    failed_only: bool = typer.Option(False, "--failed_only"),
):
    dag = _ensure_dag_exists(job_id)
    if min_execution_date:
        min_execution_date = dateutil.parser.parse(min_execution_date)
    if max_execution_date:
        max_execution_date = dateutil.parser.parse(max_execution_date)
    AirflowDbService.rerun_job_run(dag, run_id, min_execution_date, max_execution_date, failed_only)


@cli.command()
def rerun_task_run(
    job_id: int = typer.Option(..., "--job_id"),
    run_id: str = typer.Option(None, "--run_id"),
    node_key: str = typer.Option(..., "--node_key"),
    include_upstream: bool = typer.Option(False, "--include_upstream"),
    include_downstream: bool = typer.Option(False, "--include_downstream"),
    min_execution_date: str = typer.Option(None, "--min_execution_date"),
    max_execution_date: str = typer.Option(None, "--max_execution_date"),
    failed_only: bool = typer.Option(False, "--failed_only"),
):
    dag = _ensure_dag_exists(job_id)
    if min_execution_date:
        min_execution_date = dateutil.parser.parse(min_execution_date)
    if max_execution_date:
        max_execution_date = dateutil.parser.parse(max_execution_date)
    AirflowDbService.rerun_task_run(
        dag=dag,
        run_id=run_id,
        node_key=node_key,
        min_execution_date=min_execution_date,
        max_execution_date=max_execution_date,
        include_upstream=include_upstream,
        include_downstream=include_downstream,
        failed_only=failed_only,
    )


@cli.command()
def init_airflow_tables():
    AirflowDbService.init_airflow_tables()


@cli.command()
def stop_dev_run(job_id: int = typer.Option(..., "--job_id")):
    logger.info(f"start stop dev run job_id: {job_id}")
    dag = _ensure_dag_exists(job_id)

    AirflowDbService.mark_dag_run_failed(dag, whole_dag=True)


@cli.command()
def start_dev_run(
    job_id: int = typer.Option(..., "--job_id"),
    execution_date: str = typer.Option(..., "--execution_date", callback=to_local_datetime),
):
    logger.info(f"start stop dev run job_id: {job_id}")
    dag = _ensure_dag_exists(job_id)

    AirflowDbService.update_dag(dag)
    # AirflowDbService.mark_dag_run_failed(dag, whole_dag=True)
    AirflowDbService.delete_whole_dag_dr_ti(dag)
    AirflowDbService.activate_dag(dag)
    AirflowDbService.trigger_job_run(dag, execution_date, False, False, "manual")


@cli.command()
def terminate_task_run(
    job_id: int = typer.Option(..., "--job_id"),
    run_id: str = typer.Option(..., "--run_id"),
    node_key: str = typer.Option(..., "--node_key"),
):
    dag = _ensure_dag_exists(job_id)
    AirflowDbService.terminate_task_run(dag, run_id, node_key)


@cli.command()
def mark_task_run(
    job_id: int = typer.Option(..., "--job_id"),
    bundle_tasks: str = typer.Option(..., "--bundle_tasks"),
    status: str = typer.Option(..., "--status"),
):
    dag = _ensure_dag_exists(job_id)
    bundle_tasks: list[BundleTask] = [BundleTask(**bt) for bt in json.loads(bundle_tasks)]
    status = TaskInstanceState.SUCCESS if status == "completed" else TaskInstanceState.FAILED

    for bundle_task in bundle_tasks:
        AirflowDbService._set_task_run_state(
            dag=dag,
            run_id=bundle_task.run_id,
            node_key=bundle_task.node_key,
            state=status,
        )


@cli.command()
def mark_job_run(
    job_id: int = typer.Option(..., "--job_id"),
    run_ids: str = typer.Option(..., "--run_ids"),
    status: str = typer.Option(..., "--status"),
):
    dag = _ensure_dag_exists(job_id)
    run_ids: list[str] = json.loads(run_ids)

    for run_id in run_ids:
        if status == "completed":
            AirflowDbService.mark_dag_run_success(dag, run_id)
        else:
            AirflowDbService.mark_dag_run_failed(dag, run_id)


@cli.command()
def mark_job_run_queued(
    job_id: int = typer.Option(..., "--job_id"),
    run_ids: str = typer.Option(..., "--run_ids"),
):
    dag = _ensure_dag_exists(job_id)
    run_ids: list[str] = json.loads(run_ids)

    for run_id in run_ids:
        AirflowDbService.mark_dag_run_queued(dag, run_id)


if __name__ == "__main__":
    cli()
