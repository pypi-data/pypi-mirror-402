"""Flink Stream API endpoints for Recurve Data Platform"""

from fastapi import APIRouter
from loguru import logger

from recurvedata.executors.utils import run_with_result_handling_v2
from recurvedata.server.stream.flink.schema import (
    CancelJobPayload,
    CancelJobResponse,
    CreateJobPayload,
    CreateJobResponse,
    GetJobDetailsResponse,
    GetJobsResponse,
)
from recurvedata.server.stream.flink.service import FlinkService

router = APIRouter()


@router.post("/create-job")
async def create_job(*, payload: CreateJobPayload) -> CreateJobResponse:
    """
    Create a new Flink CDC streaming job

    This endpoint creates a new change data capture (CDC) job that streams data
    from a source database to a target database/warehouse in real-time using Apache Flink.

    Args:
        payload: Job configuration including source, sink, and Flink settings

    Returns:
        ResponseModel containing job creation response with job_id and status
    """
    logger.info(f"Creating Flink job: {payload.job_name}")

    res = await run_with_result_handling_v2(FlinkService.create_job, None, payload)

    logger.info(f"Flink job creation completed: job_name={payload.job_name}, status={res.ok}")
    return res


@router.post("/cancel-job")
async def cancel_job(*, payload: CancelJobPayload) -> CancelJobResponse:
    """
    Cancel a running Flink CDC job

    This endpoint cancels a currently running Flink job. The cancellation can be
    Args:
        payload: Job cancellation configuration with job_id and flink_connection_name
    """
    logger.info(f"Canceling Flink job: job_id={payload.job_id}, flink_connection_name={payload.flink_connection_name}")

    res = await run_with_result_handling_v2(FlinkService.cancel_job, None, payload)

    logger.info(f"Flink job cancellation completed: job_id={payload.job_id}, status={res.ok}")
    return res


@router.get("/get-job-details")
async def get_job_details(*, project_id: int, flink_connection_name: str, job_id: str) -> GetJobDetailsResponse:
    """
    Get detailed information about a specific Flink job

    This endpoint retrieves comprehensive details about a Flink job including
    current status, metrics, checkpoints, exceptions, and configuration.

    Args:
        job_id: The unique identifier of the Flink job
        project_id: project ID to filter jobs
        flink_connection_name: Flink connection name to filter jobs

    Returns:
        ResponseModel containing detailed job information
    """
    logger.info(f"Getting Flink job details: {job_id}")

    res = await run_with_result_handling_v2(
        FlinkService.get_job_details, None, project_id, flink_connection_name, job_id
    )

    logger.info(f"Retrieved Flink job details: job_id={job_id}, status={res.ok}")
    return res


@router.get("/get-jobs")
async def get_jobs(*, project_id: int, flink_connection_name: str) -> GetJobsResponse:
    """
    List all Flink CDC jobs, optionally filtered by project

    This endpoint returns a list of all Flink jobs with summary information.
    Jobs can be filtered by project_id if provided.

    Args:
        project_id: Optional project ID to filter jobs
        flink_connection_name: Flink connection name to filter jobs

    Returns:
        ResponseModel containing list of job summaries
    """
    logger.info(f"Listing Flink jobs: project_id={project_id}")

    res = await run_with_result_handling_v2(
        FlinkService.list_jobs,
        None,
        project_id,
        flink_connection_name,
    )

    logger.info(f"Listed Flink jobs: project_id={project_id}, count={len(res.data) if res.data else 0}")
    return res
