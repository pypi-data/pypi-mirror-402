from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from recurvedata.schedulers.schemas import BundleTask


class DependsOnJob(BaseModel):
    project_id: int
    job_id: int
    node_key: list[str]
    timeout: int


class TriggerJobRunRequest(BaseModel):
    job_id: int
    execution_date: str
    include_past: Optional[bool] = False
    include_future: Optional[bool] = False
    run_type: Optional[str] = None
    conf: Optional[dict[str, Any]] = None


class RerunJobRunRequest(BaseModel):
    job_id: int
    run_id: str | None = None
    min_execution_date: str | None = None
    max_execution_date: str | None = None
    failed_only: bool = False


class RerunTaskRunRequest(BaseModel):
    job_id: int
    node_key: str
    run_id: str | None = None
    min_execution_date: str | None = None
    max_execution_date: str | None = None
    include_upstream: bool = False
    include_downstream: bool = False
    failed_only: bool = False


class TerminateTaskRunRequest(BaseModel):
    job_id: int
    run_id: str
    node_key: str


class DeleteDagRequest(BaseModel):
    job_name: str


class StartDevRunRequest(BaseModel):
    execution_date: datetime


class CreateDagRequest(BaseModel):
    is_active: bool


class MarkTaskRunRequest(BaseModel):
    job_id: int
    bundle_tasks: list[BundleTask]
    status: str


class MarkJobRunRequest(BaseModel):
    job_id: int
    run_ids: list[str]
    status: str


class MarkJobRunQueuedRequest(BaseModel):
    job_id: int
    run_ids: list[str]
