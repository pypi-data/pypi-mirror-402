from fastapi import APIRouter
from loguru import logger

from recurvedata.core.tracing import Tracing
from recurvedata.executors.schemas import (
    ColumnListPayload,
    ConnectionRuntimePayload,
    ResponseModel,
    TableListPayload,
    TestConnectionPayload,
)
from recurvedata.executors.service.connector import ConnectionService
from recurvedata.executors.utils import run_with_result_handling_v2
from recurvedata.server.connector.guanyuan_bi.api import router as guanyuan_bi_router
from recurvedata.server.connector.schemas import (
    ListColumnsResponse,
    ListDatabasesResponse,
    ListFullDatabasesResponse,
    ListTablesResponse,
    TestConnectionResponse,
)

tracer = Tracing()
router = APIRouter()
router.include_router(guanyuan_bi_router)


@router.post("/test-connection")
@tracer.create_span(sampling_rate=0.1)
async def test_connection(*, payload: TestConnectionPayload) -> TestConnectionResponse:
    logger.info(f"test_connection: {payload.connection_type}")

    res: ResponseModel = await run_with_result_handling_v2(
        ConnectionService.test_connection, payload.timeout, payload.connection_type, payload.config
    )
    logger.info("finish test_connection")
    return TestConnectionResponse.model_validate(res.model_dump())


@router.post("/list-databases")
@tracer.create_span(sampling_rate=0.1)
async def list_databases(*, payload: ConnectionRuntimePayload) -> ListDatabasesResponse:
    logger.info(f"list_databases: {payload.connection_type}")
    res: ResponseModel = await run_with_result_handling_v2(
        ConnectionService.list_databases, None, payload.connection_type, payload.config
    )
    logger.info("finish list_databases")
    return ListDatabasesResponse.model_validate(res.model_dump())


@router.post("/list-tables")
@tracer.create_span(sampling_rate=0.1)
async def list_tables(*, payload: TableListPayload) -> ListTablesResponse:
    logger.info(f"list_tables: {payload.connection_type} {payload.database}")
    res: ResponseModel = await run_with_result_handling_v2(
        ConnectionService.list_tables, None, payload.connection_type, payload.config, payload.database
    )
    logger.info("finish list_tables")
    return ListTablesResponse.model_validate(res.model_dump())


@router.post("/list-columns")
@tracer.create_span(sampling_rate=0.1)
async def list_columns(*, payload: ColumnListPayload) -> ListColumnsResponse:
    logger.info(f"list_columns: {payload.connection_type} {payload.database} {payload.table}")
    res: ResponseModel = await run_with_result_handling_v2(
        ConnectionService.list_columns, None, payload.connection_type, payload.config, payload.database, payload.table
    )
    logger.info("finish list_columns")
    return ListColumnsResponse.model_validate(res.model_dump())


@router.post("/list-full-databases")
@tracer.create_span(sampling_rate=0.1)
async def list_full_databases(*, payload: ConnectionRuntimePayload) -> ListFullDatabasesResponse:
    logger.info(f"list_full_databases: {payload.connection_type}")
    res: ResponseModel = await run_with_result_handling_v2(
        ConnectionService.list_full_databases, None, payload.connection_type, payload.config
    )
    logger.info("finish list_full_databases")
    return ListFullDatabasesResponse.model_validate(res.model_dump())
