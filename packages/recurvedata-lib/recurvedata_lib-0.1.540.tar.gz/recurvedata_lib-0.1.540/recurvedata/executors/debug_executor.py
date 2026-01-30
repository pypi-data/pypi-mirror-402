import datetime
import logging
from typing import Any, Optional

import pendulum

from recurvedata.connectors.service import PigeonDataSource as DataSource
from recurvedata.consts import ETLExecutionStatus, ScheduleType
from recurvedata.executors.client import ExecutorClient
from recurvedata.executors.executor import Executor
from recurvedata.executors.models import ExecutorDag, ExecutorNode
from recurvedata.executors.schemas import DebugLogRecord, WorkflowNodeItem
from recurvedata.operators.task import BaseTask
from recurvedata.utils.dataclass import init_dataclass_from_dict

logger = logging.getLogger(__name__)


class DebugExecutor(Executor):
    """
    init sdk
    add sdk to context
    fetch node conf using sdk
    init Dag&Node
    """

    def __init__(
        self,
        workflow_id: int,
        node_key: str,
        schedule_type: ScheduleType,
        schedule_interval: str,
        execution_date: datetime.datetime,
        timezone: str,
        celery_task_id: str,
    ):
        self.project_id: int = None
        self.workflow_id = workflow_id
        self.node_key = node_key
        self.schedule_type = schedule_type
        self.schedule_interval = schedule_interval
        self.execution_date = execution_date
        self.timezone = pendulum.timezone(timezone)
        self.celery_task_id = celery_task_id
        self.client: ExecutorClient = ExecutorClient()
        self.dag: ExecutorDag = None
        self.node: ExecutorNode = None
        self.init_dag_node()
        self.register_context()

    def _init_task_instance_on_task_start(self, task: BaseTask):
        pass

    def _update_task_instance_on_task_finish(
        self,
        task: BaseTask,
        ti_id: int,
        task_status: ETLExecutionStatus,
        meta: Any,
        error: Exception,
        error_stack: Optional[str],
    ):
        pass

    def _get_connection_by_name(self, project_id: int, connection_name: str) -> DataSource:
        connection = self.client.get_connection(project_id=project_id, connection_name=connection_name)
        return DataSource(connection_type=connection.type, name=connection.name, data=connection.data)

    def init_dag_node(self):
        logger.info(f"start init dag node {self.workflow_id} {self.node_key}")
        api_response: WorkflowNodeItem = self.client.get_debug_node(self.workflow_id, self.node_key)
        self.project_id = api_response.project_id
        self.dag: ExecutorDag = ExecutorDag(
            id=int(self.workflow_id),
            project_id=int(self.project_id),
            name=api_response.workflow_name,
            scheduler_type=self.schedule_type,
            schedule_interval=self.schedule_interval,
            timezone=self.timezone,
            owner="debug",
        )

        self.node: ExecutorNode = init_dataclass_from_dict(ExecutorNode, api_response.model_dump(), dag=self.dag)
        self.node.variable = self.init_variables()

    def run_impl(self):
        logger.info(f"start debug {self.workflow_id}.{self.node.name}, {self.node.operator}")
        operator = self.init_operator()
        operator.execute()
        logger.info(f"finish debug {self.workflow_id}.{self.node.name}, {self.node.operator}")

    def _send_logs(self, message: str):
        self.client.send_back_debug_logs(
            DebugLogRecord(
                workflow_id=self.workflow_id,
                node_key=self.node_key,
                celery_task_id=self.celery_task_id,
                logs=[message],
            )
        )
