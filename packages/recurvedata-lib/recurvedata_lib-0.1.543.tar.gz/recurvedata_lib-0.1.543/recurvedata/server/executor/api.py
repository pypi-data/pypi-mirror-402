from fastapi import APIRouter
from loguru import logger

from recurvedata.core.tracing import Tracing
from recurvedata.executors.schemas import ResponseModel
from recurvedata.executors.utils import run_with_result_handling_v2
from recurvedata.server.executor.schemas import (
    ValidatePythonScriptPayload,
    ValidatePythonScriptResponse,
)
from recurvedata.server.executor.service import ExecutorService

tracer = Tracing()
router = APIRouter()


@router.post("/validate-python-script")
@tracer.create_span(sampling_rate=0.1)
async def validate_python_script(*, payload: ValidatePythonScriptPayload) -> ValidatePythonScriptResponse:
    """
    Validate Python script by executing it in the configured Python environment.
    
    This endpoint runs the Python code using the same infrastructure as PythonOperator,
    including proper environment setup and requirements installation.
    """
    logger.info(f"validate_python_script: project_id={payload.project_id}, python_env={payload.python_env}")

    res: ResponseModel = await run_with_result_handling_v2(
        ExecutorService.validate_python_script,
        payload.timeout,
        payload.project_id,
        payload.python_code,
        payload.python_env,
    )
    
    logger.info("finish validate_python_script")
    return ValidatePythonScriptResponse.model_validate(res.model_dump())
