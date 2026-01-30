from fastapi import APIRouter

from recurvedata.core.tracing import Tracing
from recurvedata.dbt.schemas import PreviewResponseWithError
from recurvedata.executors.schemas import ResponseModel
from recurvedata.executors.utils import run_with_result_handling_v2
from recurvedata.server.data_service.schemas import (
    DirectQueryPayload,
    DownloadPayload,
    DownloadResponseWithError,
    FetchCountPayload,
    PreviewPayload,
    PreviewTotalResponseWithError,
    SqlValidationPayload,
    SqlValidationResponseWithError,
)
from recurvedata.server.data_service.service import DataServiceService
from recurvedata.utils.sql import trim_replace_special_character

tracer = Tracing()
router = APIRouter()


@router.post("/preview")
@tracer.create_span(sampling_rate=0.1)
async def preview(*, payload: PreviewPayload) -> PreviewResponseWithError:
    sql = trim_replace_special_character(payload.sql, strip_sufix=True)

    service = DataServiceService(
        project_id=payload.project_id,
        project_connection_id=payload.project_connection_id,
    )
    res: ResponseModel = await run_with_result_handling_v2(
        service.preview,
        sql=sql,
        limit=payload.limit,
        no_data=payload.no_data,
        orders=payload.orders,
    )

    return PreviewResponseWithError.model_validate(res.model_dump())


@router.post("/download")
@tracer.create_span(sampling_rate=0.1)
async def download(*, payload: DownloadPayload) -> DownloadResponseWithError:
    sql = trim_replace_special_character(payload.sql, strip_sufix=True)

    service = DataServiceService(
        project_id=payload.project_id,
        project_connection_id=payload.project_connection_id,
    )
    res: ResponseModel = await run_with_result_handling_v2(
        service.download,
        storage_type=payload.storage_type,
        storage_options=payload.storage_options,
        sql=sql,
        orders=payload.orders,
        fields=payload.fields,
        file_type=payload.file_type,
        file_name=payload.file_name,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
        project_id=payload.project_id,
    )

    return DownloadResponseWithError.model_validate(res.model_dump())


@router.post("/preview-total")
@tracer.create_span(sampling_rate=0.1)
async def preview_total(*, payload: PreviewPayload) -> PreviewTotalResponseWithError:
    sql = trim_replace_special_character(payload.sql, strip_sufix=True)

    service = DataServiceService(
        project_id=payload.project_id,
        project_connection_id=payload.project_connection_id,
    )
    res = await run_with_result_handling_v2(
        service.preview_total,
        sql=sql,
        limit=payload.limit,
        no_data=payload.no_data,
        orders=payload.orders,
        offset=payload.offset,
    )

    return PreviewTotalResponseWithError.model_validate(res.model_dump())


@router.post("/fetch-count")
@tracer.create_span(sampling_rate=0.1)
async def fetch_count(*, payload: FetchCountPayload) -> dict:
    sql = trim_replace_special_character(payload.sql, strip_sufix=True)

    service = DataServiceService(
        project_id=payload.project_id,
        project_connection_id=payload.project_connection_id,
    )
    res: ResponseModel = await run_with_result_handling_v2(
        service.fetch_count,
        sql=sql,
    )

    return res.model_dump()


@router.post("/validate-sql")
@tracer.create_span(sampling_rate=0.1)
async def validate_sql(*, payload: SqlValidationPayload) -> SqlValidationResponseWithError:
    """
    Validate SQL by executing it and checking for syntax/runtime errors.
    Supports any SQL statement type including DDL, DML, and SELECT.
    """
    sql = trim_replace_special_character(payload.sql, strip_sufix=True)

    service = DataServiceService(
        project_id=payload.project_id,
        project_connection_id=payload.project_connection_id,
    )
    res: ResponseModel = await run_with_result_handling_v2(
        service.validate_sql,
        sql=sql,
        limit=payload.limit,
    )

    return SqlValidationResponseWithError.model_validate(res.model_dump())


@router.post("/direct-query")
@tracer.create_span(sampling_rate=0.1)
async def direct_query(*, payload: DirectQueryPayload) -> PreviewResponseWithError:
    """
    Execute SQL directly on a connection without any limitations or modifications.
    This endpoint accepts connection details and SQL, returning raw results.
    """
    # Create a minimal service instance (no project/connection ID needed for direct queries)
    service = DataServiceService(project_id=0, project_connection_id=0)

    res: ResponseModel = await run_with_result_handling_v2(
        service.direct_query,
        connection_type=payload.connection.type,
        connection_data=payload.connection.data,
        sql=payload.sql,
        limit=payload.limit,
        offset=payload.offset,
    )

    return PreviewResponseWithError.model_validate(res.model_dump())
