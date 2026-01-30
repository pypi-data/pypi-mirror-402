from recurvedata.client import Client
from recurvedata.schedulers.schemas import JobListResponse, TaskStatusCursor, WorkflowNodeDebugDetail
from recurvedata.utils import get_env_id


class SchedulerClient(Client):
    def list_jobs(self, sharding_size: int = None, sharding_key: int = None) -> JobListResponse:
        if not sharding_size:
            sharding_size = 1
            sharding_key = 0

        params = {
            "env_id": get_env_id(),
            "sharding_key": sharding_key,
            "sharding_size": sharding_size,
        }

        return self.request("GET", path="/api/scheduler/jobs", response_model_class=JobListResponse, params=params)

    def get_task_status_cursor(self) -> TaskStatusCursor:
        params = {"env_id": get_env_id()}
        return self.request(
            "GET", path="/api/scheduler/task-status-cursor", response_model_class=TaskStatusCursor, params=params
        )

    def sync_task_status(self, job_runs: list[dict] | None = None, task_runs: list[dict] | None = None):
        params = {"env_id": get_env_id()}
        payload = {
            "job_runs": job_runs,
            "task_runs": task_runs,
        }
        return self.request("POST", path="/api/scheduler/sync-task-status", params=params, json=payload)

    def get_workflow_node_debug_detail(self, workflow_id: int, node_key: str) -> WorkflowNodeDebugDetail:
        params = {
            "env_id": get_env_id(),
            "workflow_id": workflow_id,
            "node_key": node_key,
        }
        return self.request(
            "GET",
            path="/api/scheduler/workflow-node-debug-detail",
            response_model_class=WorkflowNodeDebugDetail,
            params=params,
        )

    def on_job_run_finished(self, job_run_result: dict):
        params = {"env_id": get_env_id()}
        payload = {
            "job_id": job_run_result["job_id"],
            "run_id": job_run_result["run_id"],
            "task_info_map": job_run_result["task_info_map"],
            "state": job_run_result["state"],
            "data_interval_end": job_run_result["data_interval_end"],
        }
        return self.request("POST", path="/api/scheduler/on-job-run-finished", params=params, json=payload)
