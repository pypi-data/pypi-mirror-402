import os
import traceback
from typing import Any, Generic, Optional, Self, TypeVar

from pydantic import BaseModel, Field

from recurvedata.consts import ETLExecutionStatus, Operator, ScheduleType
from recurvedata.exceptions import RecurveException, WrapRecurveException
from recurvedata.executors.utils import get_airflow_run_id, get_airflow_try_number, get_recurve_node_key

T = TypeVar("T")


class JobNodeItem(BaseModel):
    id: int = Field(default=None)
    node_key: str
    project_id: int
    job_id: int
    job_name: str
    workflow_id: int
    workflow_name: str
    job_schedule_type: ScheduleType
    job_schedule_interval: str
    job_timezone: str
    job_owner: str
    name: str
    operator: Operator
    config: dict
    variable: dict[str, Any]
    job_variable: dict[str, Any]
    full_refresh_models: bool = False
    skip_data_tests: bool = False
    retries: int | None = None
    retry_delay: int | None = None


class WorkflowNodeItem(BaseModel):
    id: int = Field(default=None, title="Node ID")
    node_key: str
    project_id: int
    workflow_id: int
    workflow_version: str
    workflow_name: str
    name: str = Field(title="Node Name")
    operator: Operator
    config: dict
    variable: dict[str, Any]


class ConnectionItem(BaseModel):
    type: str
    name: str
    display_name: str
    database: str
    database_schema: str | None = None
    data: dict
    description: str | None

    def model_post_init(self, context: dict):
        if self.database:
            self.data["database"] = self.database
        if self.database_schema:
            self.data["schema"] = self.database_schema


class TaskInstanceStart(BaseModel):
    job_id: int
    node_id: int
    operator: Operator = Field(title="Node Operator", description="节点的 Operator 类型")
    task: str = Field(title="Task Name", description="节点的任务名称")
    stage: Optional[str] = Field(default=None, title="Stage", description="任务运行阶段")
    execution_date: str = Field(title="Execution Date", description="调度时间")
    rendered_config: dict = Field(title="Rendered Config", description="任务 Config, 已渲染")
    start_time: str = Field(title="Task Start Time", description="任务开始时间")
    hostname: Optional[str] = Field(default=None, title="Machine Host Name", description="任务所在的机器 hostname")
    pid: Optional[int] = Field(default=None, title="Process ID", description="任务进程 ID")


class TaskInstanceStartResponse(BaseModel):
    task_instance_id: int = Field(title="Task Instance ID", description="Task Instance id")


class TaskInstanceEnd(BaseModel):
    job_id: int
    node_id: int
    run_id: str
    end_time: str
    execution_date: str
    meta: Optional[Any]
    traceback: Optional[Any]
    status: Optional[ETLExecutionStatus]

    current_retry_number: Optional[int]
    max_retry_number: Optional[int]
    link_workflow_id: Optional[int]
    link_node_id: Optional[int]
    data_interval_end: Optional[str] = None


class TaskLogRecord(BaseModel):
    job_id: int
    node_key: str
    run_id: str
    try_number: int
    logs: list[str]

    @classmethod
    def init(cls, job_id: int, logs: list[str]) -> "TaskLogRecord":
        return cls(
            job_id=job_id,
            node_key=get_recurve_node_key(),
            run_id=get_airflow_run_id(),
            try_number=get_airflow_try_number(),
            logs=logs,
        )


class DebugLogRecord(BaseModel):
    workflow_id: int
    node_key: str
    celery_task_id: str
    logs: list[str]

    @classmethod
    def init(cls, workflow_id: int, node_key: str, celery_task_id: str, logs: list[str]) -> "DebugLogRecord":
        return cls(
            workflow_id=workflow_id,
            node_key=node_key,
            celery_task_id=celery_task_id,
            logs=logs,
        )


class DebugStart(BaseModel):
    workflow_id: int
    node_key: str
    celery_task_id: str


class DebugEnd(DebugStart):
    is_success: bool


class ConnectionRuntimePayload(BaseModel):
    connection_type: str
    config: dict
    result_filename: str | None = None


class TestConnectionPayload(ConnectionRuntimePayload):
    timeout: int = 30


class ListDatabases(BaseModel):
    items: list[str] | None


class ResponseError(BaseModel):
    code: str
    reason: str | None
    exception: str | None = None
    traceback: str | None = None
    data: dict | str | None = None

    @classmethod
    def from_recurve_exception(cls, recurve_exception: RecurveException) -> Self:
        if recurve_exception.data:
            reason = f"{recurve_exception.code.message} {recurve_exception.data}"
        else:
            reason = recurve_exception.code.message
        if isinstance(recurve_exception, WrapRecurveException):
            exception = str(recurve_exception.exception)
        else:
            exception = None
        return cls(
            code=recurve_exception.code.code,
            reason=reason,
            exception=exception,
            traceback=traceback.format_exc(),
            data=recurve_exception.data,
        )


class ResponseModel(BaseModel, Generic[T]):
    ok: bool
    error: ResponseError | None = None
    data: T = None

    def model_dump_json_file(self, filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(self.model_dump_json(indent=2))


class ColumnItem(BaseModel):
    name: str
    type: str
    comment: str | None = None
    normalized_type: str


class TableItem(BaseModel):
    name: str


class Pagination(BaseModel, Generic[T]):
    total: int
    items: list[T]


class TableListPayload(ConnectionRuntimePayload):
    database: str


class ColumnListPayload(TableListPayload):
    table: str


class FullDatabaseItem(BaseModel):
    name: str
    tables: list[TableItem]
    views: list[TableItem]
