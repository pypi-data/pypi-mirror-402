from fastapi import APIRouter

from recurvedata.connectors.connectors.guanyuan_bi import GuanyuanBI
from recurvedata.executors.schemas import ResponseModel
from recurvedata.executors.utils import run_with_result_handling_v2
from recurvedata.server.connector.guanyuan_bi.schema import (
    GetCardsByPagePayload,
    GetCardSQLPayload,
    GetDataSetPayload,
    GetPagesPayload,
)
from recurvedata.server.connector.guanyuan_bi.service import GuanyuanBIService

router = APIRouter(prefix="/guanyuan-bi")


@router.post("/get-pages")
async def get_pages(*, payload: GetPagesPayload) -> ResponseModel:
    connector = GuanyuanBI(conf=payload.config)
    resp: ResponseModel = await run_with_result_handling_v2(GuanyuanBIService.get_pages, None, connector)
    return resp


@router.post("/get-cards-by-page")
async def get_cards_by_page(*, payload: GetCardsByPagePayload) -> ResponseModel:
    connector = GuanyuanBI(conf=payload.config)
    resp: ResponseModel = await run_with_result_handling_v2(
        GuanyuanBIService.get_cards_by_page, None, connector, payload.page_id
    )
    return resp


@router.post("/get-data-set")
async def get_data_set(*, payload: GetDataSetPayload) -> ResponseModel:
    connector = GuanyuanBI(conf=payload.config)
    resp: ResponseModel = await run_with_result_handling_v2(
        GuanyuanBIService.get_data_set, None, connector, payload.data_set_id
    )
    return resp


@router.post("/get-card-sql")
async def get_card_sql(*, payload: GetCardSQLPayload) -> ResponseModel:
    connector = GuanyuanBI(conf=payload.config)
    resp: ResponseModel = await run_with_result_handling_v2(
        GuanyuanBIService.get_card_sql, None, connector, payload.card_id
    )
    return resp
