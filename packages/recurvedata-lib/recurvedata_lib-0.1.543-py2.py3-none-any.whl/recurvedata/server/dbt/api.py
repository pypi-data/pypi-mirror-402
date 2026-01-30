import json
import tempfile

from fastapi import APIRouter
from loguru import logger

from recurvedata.config import SERVER_RESULT_STAGING_PATH
from recurvedata.core.tracing import Tracing
from recurvedata.dbt.schemas import (
    BuildPayload,
    BuildResponseWithError,
    CompilePayload,
    CompileResponseWithError,
    CompileResult,
    PreviewPayload,
    PreviewResponseWithError,
)
from recurvedata.dbt.service import DbtService
from recurvedata.dbt.utils import format_var
from recurvedata.executors.utils import run_with_result_handling
from recurvedata.utils.sql import trim_replace_special_character

tracer = Tracing()
router = APIRouter()


@router.post("/compile")
@tracer.create_span(sampling_rate=0.1, context_payload_name="payload")
def compile(*, payload: CompilePayload) -> CompileResponseWithError:
    sql = trim_replace_special_character(payload.sql)
    service = DbtService(
        project_id=payload.project_id,
        project_connection_name=payload.alias,
        force_regenerate_dir=payload.force_regenerate_dir,
        need_fetch_variable=True,
    )

    result_file_name = tempfile.mktemp(dir=SERVER_RESULT_STAGING_PATH)
    logger.info(f"compile result_file_name: {result_file_name}, payload: {payload}")

    run_with_result_handling(
        service.compile, inline_sql=sql, result_filename=result_file_name, validate_sql=payload.validate_sql
    )
    with open(result_file_name, "r") as temp_file:
        data: dict = json.load(temp_file)

    logger.info(f"finish compile {result_file_name}")

    return CompileResponseWithError.model_validate(data)


@router.post("/preview")
@tracer.create_span(sampling_rate=0.1, context_payload_name="payload")
async def preview(*, payload: PreviewPayload) -> PreviewResponseWithError:
    sql = trim_replace_special_character(payload.sql, strip_sufix=True)
    service = DbtService(
        project_id=payload.project_id,
        project_connection_name=payload.alias,
        force_regenerate_dir=payload.force_regenerate_dir,
        need_fetch_variable=True,
    )

    result_file_name = tempfile.mktemp(dir=SERVER_RESULT_STAGING_PATH)
    logger.info(f"preview result_file_name: {result_file_name}, payload: {payload}")

    run_with_result_handling(
        service.preview,
        inline_sql=sql,
        limit=payload.limit,
        result_filename=result_file_name,
        no_data=payload.no_data,
        is_compiled=payload.is_compiled,
    )
    with open(result_file_name, "r") as temp_file:
        data: dict = json.load(temp_file)

    logger.info(f"finish preview {result_file_name}")

    return PreviewResponseWithError.model_validate(data)


@router.post("/build")
@tracer.create_span(sampling_rate=0.1, context_payload_name="payload")
def build(*, payload: BuildPayload) -> BuildResponseWithError:
    service = DbtService(
        project_id=payload.project_id,
        project_connection_name=payload.alias,
        force_regenerate_dir=payload.force_regenerate_dir,
        need_fetch_variable=True,
    )
    service.prepare()

    logger.info(f"build data model {payload.model_name}")

    var_str = format_var(service, service.variables | (payload.variables or {}))

    def run_model(model_name: str, dbt_vars: str = None, full_refresh: bool = False):
        compiled_code, _ = service._run_model(
            model_name=model_name,
            dbt_vars=dbt_vars,
            full_refresh=full_refresh,
        )
        return CompileResult(compiled_sql=compiled_code)

    result_file_name = tempfile.mktemp(dir=SERVER_RESULT_STAGING_PATH)
    run_with_result_handling(
        run_model,
        model_name=payload.model_name,
        dbt_vars=var_str,
        full_refresh=payload.full_refresh,
        result_filename=result_file_name,
    )
    with open(result_file_name, "r") as temp_file:
        data: dict = json.load(temp_file)
    logger.info(f"finished build model {payload.model_name}")
    return BuildResponseWithError.model_validate(data)
