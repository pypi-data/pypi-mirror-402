import datetime
from typing import Any, Optional

from recurvedata.client import Client
from recurvedata.config import RECURVE_EXECUTOR_PYENV_NAME
from recurvedata.consts import ETLExecutionStatus, Operator
from recurvedata.executors.schemas import (
    ConnectionItem,
    DebugEnd,
    DebugLogRecord,
    DebugStart,
    JobNodeItem,
    TaskInstanceEnd,
    TaskInstanceStart,
    TaskInstanceStartResponse,
    TaskLogRecord,
    WorkflowNodeItem,
)
from recurvedata.utils import get_env_id


class ExecutorClient(Client):
    def get_node(self, job_id: int, node_id: int) -> JobNodeItem:
        params = {
            "env_id": get_env_id(),
            "job_id": job_id,
        }

        return self.request(
            "GET", path=f"/api/executor/node/{node_id}", response_model_class=JobNodeItem, params=params
        )

    def get_connection(self, project_id: int, connection_name: str) -> ConnectionItem:
        params = {
            "env_id": get_env_id(),
            "name": connection_name,
            "project_id": project_id,
        }
        return self.request("GET", path="/api/executor/connection", response_model_class=ConnectionItem, params=params)

    def task_instance_start(
        self,
        job_id: int,
        node_id: int,
        operator: Operator,
        task: str,
        execution_date: datetime.datetime,
        rendered_config: dict,
        start_time: datetime.datetime,
        hostname: Optional[str],
        pid: Optional[int],
    ):
        payload = TaskInstanceStart(
            job_id=job_id,
            node_id=node_id,
            task=task,
            operator=operator,
            execution_date=execution_date.isoformat(),
            rendered_config=rendered_config,
            start_time=start_time.isoformat(),
            hostname=hostname,
            pid=pid,
        ).model_dump()
        params = {
            "env_id": get_env_id(),
        }
        return self.request(
            "POST",
            path="/api/executor/start",
            response_model_class=TaskInstanceStartResponse,
            params=params,
            json=payload,
        )

    def task_instance_end(
        self,
        meta: Any,
        traceback: Any,
        status: ETLExecutionStatus,
        end_time: datetime.datetime,
        execution_date: datetime.datetime,
        job_id: int,
        node_id: int,
        run_id: str,
        current_retry_number: Optional[int],
        max_retry_number: Optional[int],
        link_workflow_id: Optional[int],
        link_node_id: Optional[int],
        data_interval_end: Optional[str],
        **kwargs,
    ):
        payload = TaskInstanceEnd(
            job_id=job_id,
            node_id=node_id,
            run_id=run_id,
            end_time=end_time.isoformat(),
            execution_date=execution_date.isoformat(),
            meta=meta,
            traceback=traceback,
            status=status,
            current_retry_number=current_retry_number,
            max_retry_number=max_retry_number,
            link_workflow_id=link_workflow_id,
            link_node_id=link_node_id,
            data_interval_end=data_interval_end,
        ).model_dump()
        params = {
            "env_id": get_env_id(),
        }
        return self.request(
            "POST",
            path="/api/executor/end",
            params=params,
            json=payload,
            timeout=10,  # todo: backend process time is slow, dispatch still wait
        )

    def get_workflow_node(self, workflow_id: int, node_id: int) -> WorkflowNodeItem:
        params = {
            "env_id": get_env_id(),
            "workflow_id": workflow_id,
        }
        return self.request(
            "GET", path=f"/api/executor/workflow_node/{node_id}", response_model_class=WorkflowNodeItem, params=params
        )

    def send_back_logs(self, record: TaskLogRecord):
        params = {
            "env_id": get_env_id(),
        }
        return self.request("POST", path="/api/executor/logs", params=params, json={"records": [record.model_dump()]})

    def send_back_debug_logs(self, record: DebugLogRecord):
        params = {
            "env_id": get_env_id(),
        }
        return self.request(
            "POST", path="/api/executor/debug_logs", params=params, json={"records": [record.model_dump()]}
        )

    def get_debug_node(self, workflow_id: int, node_key: str) -> WorkflowNodeItem:
        params = {
            "env_id": get_env_id(),
            "node_key": node_key,
        }
        return self.request(
            "GET", path=f"/api/executor/debug_node/{workflow_id}", response_model_class=WorkflowNodeItem, params=params
        )

    def debug_start(self, workflow_id: int, node_key: str, celery_task_id: str):
        payload = DebugStart(workflow_id=workflow_id, node_key=node_key, celery_task_id=celery_task_id).model_dump()
        params = {
            "env_id": get_env_id(),
        }
        return self.request(
            "POST",
            path="/api/executor/debug_start",
            params=params,
            json=payload,
        )

    def debug_end(self, workflow_id: int, node_key: str, celery_task_id: str, is_success: bool):
        payload = DebugEnd(
            workflow_id=workflow_id, node_key=node_key, celery_task_id=celery_task_id, is_success=is_success
        ).model_dump()
        params = {
            "env_id": get_env_id(),
        }
        return self.request(
            "POST",
            path="/api/executor/debug_end",
            params=params,
            json=payload,
            timeout=10,
        )

    def get_py_conn_configs(
        self,
        conn_type: str = "python",
        pyenv_name: str = RECURVE_EXECUTOR_PYENV_NAME,
        project_conn_name: str = "",
        project_id: int = 0,
    ) -> dict:
        params = {
            "conn_type": conn_type,
            "pyenv_name": pyenv_name,
            "project_conn_name": project_conn_name,
            "project_id": project_id,
        }
        return self.request("GET", path="/api/executor/python-conn-configs", params=params)
