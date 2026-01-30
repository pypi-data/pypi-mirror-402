import json
import logging
import subprocess
from typing import List

from fastapi import APIRouter

from recurvedata.exceptions import RecurveException
from recurvedata.server.schedulers.schemas import (
    CreateDagRequest,
    DeleteDagRequest,
    MarkJobRunQueuedRequest,
    MarkJobRunRequest,
    MarkTaskRunRequest,
    RerunJobRunRequest,
    RerunTaskRunRequest,
    StartDevRunRequest,
    TerminateTaskRunRequest,
    TriggerJobRunRequest,
)
from recurvedata.server.schemas import ResponseError, ResponseModel
from recurvedata.utils.date_time import to_local_datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["schedulers"])
job_router = APIRouter()
task_router = APIRouter()

# ------------------------------
# job APIs
# ------------------------------


async def _execute_scheduler_command(cmd: List[str], operation_name: str, job_id: int) -> ResponseModel:
    """
    Execute a scheduler command and return standardized response.

    Args:
        cmd: Command to execute
        operation_name: Name of the operation for logging
        job_id: Job ID for error context
    """
    is_ok = True
    error = None

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        logger.info(f"{operation_name} {job_id} result: {result.stdout}")

        if result.returncode != 0:
            logger.error(f"{operation_name} {job_id} failed: {result.stderr}")
            is_ok = False
            error = ResponseError.from_recurve_exception(RecurveException(data={"job_id": job_id}))

    except Exception as e:
        logger.error(f"{operation_name} failed: {e}")
        is_ok = False
        error = ResponseError.from_recurve_exception(RecurveException(data={"job_id": job_id}))

    return ResponseModel(ok=is_ok, error=error)


@job_router.post("/{job_id}/create")
async def create_dag(*, job_id: int, body: CreateDagRequest) -> ResponseModel:
    # First update the DAG
    update_dag_cmd = ["recurve_scheduler", "update-dag", "--job_id", str(job_id)]
    update_result = await _execute_scheduler_command(update_dag_cmd, "update dag", job_id)

    if not update_result.ok:
        return update_result

    # Then activate if requested
    if body.is_active:
        activate_result = await _execute_scheduler_command(
            ["recurve_scheduler", "activate-dag", "--job_id", str(job_id)], "activate dag", job_id
        )
        if not activate_result.ok:
            return activate_result

    logger.info(f"create dag {job_id} success")
    return ResponseModel(ok=True)


@job_router.post("/{job_id}/update")
async def update_dag(*, job_id: int) -> ResponseModel:
    update_dag_cmd = ["recurve_scheduler", "update-dag", "--job_id", str(job_id)]
    return await _execute_scheduler_command(update_dag_cmd, "update dag", job_id)


@job_router.post("/{job_id}/activate")
async def activate_dag(*, job_id: int) -> ResponseModel:
    return await _execute_scheduler_command(
        ["recurve_scheduler", "activate-dag", "--job_id", str(job_id)], "activate dag", job_id
    )


@job_router.post("/{job_id}/deactivate")
async def deactivate_dag(*, job_id: int) -> ResponseModel:
    return await _execute_scheduler_command(
        ["recurve_scheduler", "deactivate-dag", "--job_id", str(job_id)], "deactivate dag", job_id
    )


@job_router.post("/{job_id}/delete")
async def delete_dag(*, job_id: int, body: DeleteDagRequest) -> ResponseModel:
    return await _execute_scheduler_command(
        ["recurve_scheduler", "delete-dag", "--job_id", str(job_id), "--job_name", body.job_name], "delete dag", job_id
    )


@job_router.post("/trigger-job-run")
async def trigger_job_run(
    *,
    body: TriggerJobRunRequest,
) -> ResponseModel:
    job_id = body.job_id
    cmd = [
        "recurve_scheduler",
        "trigger-job-run",
        "--job_id",
        str(job_id),
        "--execution_date",
        body.execution_date,
    ]

    if body.include_past:
        cmd.append("--include_past")
    if body.include_future:
        cmd.append("--include_future")
    if body.run_type:
        cmd.extend(["--run_type", body.run_type])
    if body.conf:
        cmd.extend(["--conf", json.dumps(body.conf)])

    return await _execute_scheduler_command(cmd, "trigger job run", job_id)


@job_router.post("/rerun-job")
async def rerun_job_run(
    *,
    body: RerunJobRunRequest,
) -> ResponseModel:
    job_id = body.job_id
    cmd = ["recurve_scheduler", "rerun-job-run", "--job_id", str(job_id)]

    if body.run_id:
        cmd.append("--run_id")
        cmd.append(body.run_id)

    if body.min_execution_date:
        cmd.append("--min_execution_date")
        cmd.append(body.min_execution_date)
    if body.max_execution_date:
        cmd.append("--max_execution_date")
        cmd.append(body.max_execution_date)
    if body.failed_only:
        cmd.append("--failed_only")

    return await _execute_scheduler_command(cmd, "rerun job run", job_id)


@job_router.post("/{job_id}/stop-dev-run")
async def stop_dev_run(*, job_id: int) -> ResponseModel:
    logger.info(f"start stop dev run job_id: {job_id}")
    return await _execute_scheduler_command(
        ["recurve_scheduler", "stop-dev-run", "--job_id", str(job_id)], "stop dev run", job_id
    )


@job_router.post("/{job_id}/start-dev-run")
async def start_dev_run(*, job_id: int, body: StartDevRunRequest) -> ResponseModel:
    logger.info(f"start start dev run job_id: {job_id}")
    execution_date = to_local_datetime(body.execution_date)
    return await _execute_scheduler_command(
        [
            "recurve_scheduler",
            "start-dev-run",
            "--job_id",
            str(job_id),
            "--execution_date",
            execution_date.isoformat(),
        ],
        "start dev run",
        job_id,
    )


@job_router.post("/mark-job")
async def mark_job_run(
    *,
    body: MarkJobRunRequest,
) -> ResponseModel:
    job_id = body.job_id
    cmd = [
        "recurve_scheduler",
        "mark-job-run",
        "--job_id",
        str(job_id),
        "--run_ids",
        json.dumps(body.run_ids),
        "--status",
        body.status,
    ]
    return await _execute_scheduler_command(cmd, "mark job run", job_id)


@job_router.post("/mark-job-queued")
async def mark_job_run_queued(
    *,
    body: MarkJobRunQueuedRequest,
) -> ResponseModel:
    job_id = body.job_id
    cmd = [
        "recurve_scheduler",
        "mark-job-run-queued",
        "--job_id",
        str(job_id),
        "--run_ids",
        json.dumps(body.run_ids),
    ]
    return await _execute_scheduler_command(cmd, "mark job queued", job_id)


# ------------------------------
# task APIs
# ------------------------------


@task_router.post("/rerun-task")
async def rerun_task_run(
    *,
    body: RerunTaskRunRequest,
) -> ResponseModel:
    job_id = body.job_id
    cmd = [
        "recurve_scheduler",
        "rerun-task-run",
        "--job_id",
        str(job_id),
        "--node_key",
        body.node_key,
    ]

    if body.run_id:
        cmd.append("--run_id")
        cmd.append(body.run_id)
    if body.min_execution_date:
        cmd.append("--min_execution_date")
        cmd.append(body.min_execution_date)
    if body.max_execution_date:
        cmd.append("--max_execution_date")
        cmd.append(body.max_execution_date)

    if body.include_upstream:
        cmd.append("--include_upstream")
    if body.include_downstream:
        cmd.append("--include_downstream")
    if body.failed_only:
        cmd.append("--failed_only")

    return await _execute_scheduler_command(cmd, "rerun task run", job_id)


@task_router.post("/terminate-task")
async def terminate_task_run(
    *,
    body: TerminateTaskRunRequest,
) -> ResponseModel:
    job_id = body.job_id
    return await _execute_scheduler_command(
        [
            "recurve_scheduler",
            "terminate-task-run",
            "--job_id",
            str(job_id),
            "--run_id",
            body.run_id,
            "--node_key",
            body.node_key,
        ],
        "terminate task run",
        job_id,
    )


@task_router.post("/mark-task")
async def mark_task_run(
    *,
    body: MarkTaskRunRequest,
) -> ResponseModel:
    job_id = body.job_id
    bundle_tasks = [bt.model_dump(mode="json") for bt in body.bundle_tasks]
    cmd = [
        "recurve_scheduler",
        "mark-task-run",
        "--job_id",
        str(job_id),
        "--bundle_tasks",
        json.dumps(bundle_tasks),
        "--status",
        body.status,
    ]
    return await _execute_scheduler_command(cmd, "mark task run", job_id)


# Register sub-routers
router.include_router(job_router, prefix="/jobs")
router.include_router(task_router, prefix="/tasks")
