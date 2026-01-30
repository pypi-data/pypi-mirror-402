from typing import Any, Literal

from pydantic import BaseModel, Field

from recurvedata.executors.schemas import Pagination, ResponseModel
from recurvedata.filestorage import StorageType


class PreviewPayload(BaseModel):
    sql: str
    project_id: int
    project_connection_id: int
    limit: int
    no_data: bool = False
    orders: list[dict[str, str]] | None = None
    offset: int = 0


class DownloadPayload(BaseModel):
    sql: str
    project_id: int
    project_connection_id: int
    orders: list[dict[str, str]] | None = None
    fields: list[dict] | None = None
    file_name: str
    file_type: Literal["csv", "xlsx"]
    storage_type: StorageType
    storage_options: dict[str, Any]
    tenant_id: int
    user_id: int


class DownloadResult(BaseModel):
    file_name: str


class DownloadResponseWithError(ResponseModel):
    data: DownloadResult | None


class PreviewTotalResponseWithError(ResponseModel):
    data: Pagination[dict[str, Any]] | None


class FetchCountPayload(BaseModel):
    sql: str
    project_id: int
    project_connection_id: int


class SqlValidationResult(BaseModel):
    """Result of SQL validation including any type of SQL statement"""

    is_valid: bool
    compiled_sql: str
    columns: list[dict] = Field(default_factory=list)  # Column info if applicable
    data: list[list] = Field(default_factory=list)  # Data if applicable and requested
    error_message: str | None = None
    error_code: str | None = None
    error_traceback: str | None = None


class SqlValidationResponseWithError(ResponseModel):
    data: SqlValidationResult | None


class SqlValidationPayload(BaseModel):
    sql: str
    project_id: int
    project_connection_id: int
    limit: int = 0  # Default to 0 to avoid large data returns


class DirectQueryConnection(BaseModel):
    type: str
    data: dict


class DirectQueryPayload(BaseModel):
    connection: DirectQueryConnection
    sql: str
    limit: int = 100  # Default limit for direct queries
    offset: int = 0
