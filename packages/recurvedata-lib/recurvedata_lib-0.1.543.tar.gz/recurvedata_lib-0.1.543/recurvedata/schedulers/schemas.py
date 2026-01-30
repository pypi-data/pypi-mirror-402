import datetime

from pydantic import BaseModel

from recurvedata.consts import Operator, ScheduleType


class SchedulerLinkWorkflowNodeItem(BaseModel):
    link_wf_id: int
    link_wf_version: str
    link_node_id: int
    link_node_key: str
    link_node_name: str
    link_operator: Operator
    link_skip_self: bool
    link_skip_downstream: bool
    link_latest_only: bool
    link_scheduler_settings: dict | None
    plan_id: int | None = None


class SchedulerLinkNodeItem(BaseModel):
    node_id: int
    link_wf_id: int
    link_wf_version: str
    link_node_id: int
    link_node_key: str
    link_node_name: str
    link_operator: Operator
    link_skip_self: bool
    link_skip_downstream: bool
    link_latest_only: bool
    link_scheduler_settings: dict | None


class SchedulerNodeItem(BaseModel):
    id: int
    node_key: str
    name: str
    operator: Operator
    scheduler_settings: dict | None
    skip_self: bool
    skip_downstream: bool
    latest_only: bool


class JobItem(BaseModel):
    id: int
    name: str
    schedule_type: ScheduleType
    schedule_interval: str
    timezone: str | None
    workflow_version: str
    start_date: datetime.datetime | None
    end_date: datetime.datetime | None
    scheduler_settings: dict | None
    owner_username: str

    nodes: list[SchedulerNodeItem]

    graph: list
    project_id: int = None
    project_name: str = None
    workflow_id: int = None
    workflow_name: str = None

    skip_data_tests: bool = False
    retries: int | None = None
    retry_delay: int | None = None
    enable_depends_on_jobs: bool | None = False
    depends_on_jobs: list[dict] | None = None


class SchedulerLinkWorkflowItem(BaseModel):
    node_id: int
    link_wf_id: int
    link_wf_name: str
    link_wf_version: str
    link_nodes: list[SchedulerLinkWorkflowNodeItem]
    link_graph: list


class JobListResponse(BaseModel):
    jobs: list[JobItem]
    link_nodes: list[SchedulerLinkNodeItem]
    link_workflows: list[SchedulerLinkWorkflowItem]


class TaskStatusCursor(BaseModel):
    job_run: datetime.datetime | None = None
    task_run: datetime.datetime | None = None
    limit: int = 30
    sliding_time: int = 1
    unfinished: dict | None = None


class WorkflowNodeDebugDetail(BaseModel):
    celery_task_id: str | None = None
    state: str | None = None


class BundleTask(BaseModel):
    run_id: str
    node_key: str
