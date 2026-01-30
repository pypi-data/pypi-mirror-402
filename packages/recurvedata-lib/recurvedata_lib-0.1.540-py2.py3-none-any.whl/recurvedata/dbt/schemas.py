from dbt.cli.main import dbtRunnerResult
from pydantic import BaseModel, ConfigDict, Field

from recurvedata.core.consts import TRACING_CONTEXT_KEY
from recurvedata.executors.schemas import ColumnItem, ConnectionItem, ResponseModel


class CompileResult(BaseModel):
    compiled_sql: str | None = None


class PreviewResult(BaseModel):
    compiled_sql: str
    columns: list[ColumnItem]
    data: list[list]


class SingleModelLineage(BaseModel):
    upstream_model_name: str
    downstream_model_name: str
    upstream_package_name: str | None = None  # None means current project


class DbtOperatorNode(BaseModel):
    model_name: str
    config: dict


class DbtGraph(BaseModel):
    model_names: list[str]
    graph: list[SingleModelLineage]
    nodes: list[DbtOperatorNode]


class DbtGzMd5(BaseModel):
    md5: str


class AnalyticsDatabaseConnectionAndVariable(BaseModel):
    connection: ConnectionItem
    variables: dict


class CompileResponseWithError(ResponseModel):
    data: CompileResult | None


class PreviewResponseWithError(ResponseModel):
    data: PreviewResult | None


class CompilePayload(BaseModel):
    model_config = {"populate_by_name": True}

    project_id: int
    sql: str
    alias: str
    force_regenerate_dir: bool = False
    validate_sql: bool = False
    tracing_context: str | None = Field(default=None, alias=TRACING_CONTEXT_KEY)


class PreviewPayload(BaseModel):
    model_config = {"populate_by_name": True}

    sql: str
    project_id: int
    alias: str
    limit: int
    force_regenerate_dir: bool = False
    no_data: bool = False
    is_compiled: bool = False
    tracing_context: str | None = Field(default=None, alias=TRACING_CONTEXT_KEY)


class BuildPayload(BaseModel):
    model_config = {"populate_by_name": True}

    project_id: int
    model_name: str
    alias: str
    full_refresh: bool = False
    force_regenerate_dir: bool = False
    variables: dict | None = None
    tracing_context: str | None = Field(default=None, alias=TRACING_CONTEXT_KEY)


class BuildResponseWithError(ResponseModel):
    data: CompileResult | None


class RunModelResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    compiled_sql: str | None = None
    result: "dbtRunnerResult"
    run_sql: str | None = None
    run_log: str | None = None
