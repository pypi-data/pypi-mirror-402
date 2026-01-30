from enum import Enum

from pydantic import BaseModel

from recurvedata.executors.schemas import ConnectionRuntimePayload


class CardType(Enum):
    # https://api.guandata.com/apidoc/docs-site/345092/api-3471043
    CHART = "CHART"
    TEXT = "TEXT"
    IFRAME = "IFRAME"
    DRILL = "DRILL"
    PICTURE = "PICTURE"
    PARAMETER = "PARAMETER"
    SELECTOR = "SELECTOR"
    LIST_VIEW = "LIST_VIEW"
    TREE_SELECTOR = "TREE_SELECTOR"
    LAYOUT = "LAYOUT"
    CUSTOM = "CUSTOM"
    ANALYSIS = "ANALYSIS"
    MERGE_SELECTOR = "MERGE_SELECTOR"


class Page(BaseModel):
    pgId: str
    name: str
    description: str | None = None
    pgType: str
    parentDirId: str
    isDel: bool


class Card(BaseModel):
    cdType: CardType
    cdId: str
    name: str


class DataSet(BaseModel):
    dsId: str
    displayType: str
    name: str
    description: str | None = None
    config: dict


class CardResult(BaseModel):
    page_id: str
    page_name: str
    card_id: str
    card_name: str
    sql: str


class GetPagesPayload(ConnectionRuntimePayload):
    pass


class GetCardsByPagePayload(ConnectionRuntimePayload):
    page_id: str


class GetDataSetPayload(ConnectionRuntimePayload):
    data_set_id: str


class GetCardSQLPayload(ConnectionRuntimePayload):
    card_id: str
