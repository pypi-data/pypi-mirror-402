import datetime
import json
import logging
import os
import socket
from typing import TYPE_CHECKING, Any, Optional

from recurvedata.connectors.service import PigeonDataSource as DataSource
from recurvedata.consts import PROJECT_ID_KEY, ETLExecutionStatus
from recurvedata.core.templating import Renderer
from recurvedata.executors.client import ExecutorClient
from recurvedata.executors.consts import VariableType
from recurvedata.executors.models import ExecutorDag, ExecutorNode
from recurvedata.executors.schemas import JobNodeItem, TaskLogRecord
from recurvedata.executors.utils import get_airflow_run_id, update_meta_file
from recurvedata.operators import get_operator_class
from recurvedata.operators.context import context
from recurvedata.operators.task import BaseTask
from recurvedata.utils.dataclass import init_dataclass_from_dict
from recurvedata.utils.date_time import astimezone, tz_local, utcnow_aware
from recurvedata.utils.helpers import get_environment_variable, truncate_string
from recurvedata.utils.log_capture import OutputInterceptor, setup_log_handler

if TYPE_CHECKING:
    from recurvedata.operators.operator import BaseOperator

logger = logging.getLogger(__name__)


class Executor(object):
    """Executor class for running workflow nodes.

    Handles initialization and execution of workflow nodes with the following responsibilities:
    - Initializes SDK client and connects to backend services
    - Fetches node configuration and initializes DAG/Node objects
    - Sets up execution context and variables
    - Manages node execution lifecycle including logging and error handling

    Args:
        dag_slug (str): Identifier for the DAG in format "dag.{job_id}"
        node_slug (str): Identifier for the node in format "node.{node_id}-{name}"
        execution_date (str): Execution timestamp for the node run
    """

    def __init__(self, dag_slug: str, node_slug: str, execution_date: str):
        self.job_id = self._extract_job_id(dag_slug)
        self.node_id = self._extract_node_id(node_slug)
        self.client: ExecutorClient = ExecutorClient()
        self._execution_date = execution_date
        self.execution_date: datetime.datetime = None
        self.dag: ExecutorDag = None
        self.node: ExecutorNode = None
        self.init_dag_node()
        self.register_context()

    def _extract_job_id(self, dag_slug: str) -> int:
        return int(dag_slug.split(".")[-1])

    def _extract_node_id(self, node_slug: str) -> int:
        return int(node_slug.split(".")[1].split("-")[0])

    def register_context(self):
        context.client = self.client
        context.init_context(get_connection_by_name=self._get_connection_by_name)
        context.current_project_id.set(self.dag.project_id)
        context.register_function("init_task_instance_on_task_start", self._init_task_instance_on_task_start)
        context.register_function("update_task_instance_on_task_finish", self._update_task_instance_on_task_finish)

    def _init_task_instance_on_task_start(self, task: BaseTask):
        # todo: move to another place
        update_meta_file(
            task.dag.id,
            task.node.node_key,
            task.execution_date,
            {
                "operator": task.node.operator,
                "task": task.__class__.__name__,
            },
        )  # todo: move to another place

    def _prepare_task_end_payload(self) -> dict:
        return {
            "current_retry_number": get_environment_variable("AIRFLOW_RETRY_NUMBER", int),
            "max_retry_number": get_environment_variable("AIRFLOW_MAX_RETRY_NUMBER", int),
            "link_node_id": self.node.link_settings and self.node.link_settings.get("node_id"),
            "link_workflow_id": self.node.link_settings and self.node.link_settings.get("workflow_id"),
            "node_id": self.node.id,
            "execution_date": self.execution_date,
            "data_interval_end": get_environment_variable("AIRFLOW_DATA_INTERVAL_END"),
            "run_id": get_airflow_run_id(),
            "job_id": self.job_id,
        }

    def _update_task_instance_on_task_finish(
        self,
        task: BaseTask,
        ti_id: int,
        task_status: ETLExecutionStatus,
        meta: Any,
        error: Exception,
        error_stack: Optional[str],
    ):
        kwargs = self._prepare_task_end_payload()
        if task_status == ETLExecutionStatus.FAILED:
            if kwargs["max_retry_number"] and kwargs["current_retry_number"] < (kwargs["max_retry_number"] + 1):
                # airflow try_times = first time + max_retry_number
                task_status = ETLExecutionStatus.RETRY
        self.client.task_instance_end(
            meta=meta,
            traceback=error_stack and truncate_string(error_stack, 1000),
            status=task_status,
            end_time=utcnow_aware(),
            **kwargs,
        )

    def _get_connection_by_name(self, project_id: int, connection_name: str) -> DataSource:
        connection = self.client.get_connection(project_id=project_id, connection_name=connection_name)
        return DataSource(connection_type=connection.type, name=connection.name, data=connection.data)

    def init_dag_node(self):
        logger.info(f"start init dag node {self.job_id} {self.node_id}")
        api_response: JobNodeItem = self.client.get_node(self.job_id, self.node_id)

        self.dag: ExecutorDag = ExecutorDag(
            id=int(api_response.job_id),
            project_id=int(api_response.project_id),
            name=api_response.job_name,
            scheduler_type=api_response.job_schedule_type,
            schedule_interval=api_response.job_schedule_interval,
            timezone=api_response.job_timezone,
            owner=api_response.job_owner,
            workflow_id=api_response.workflow_id,
            workflow_name=api_response.workflow_name,
            full_refresh_models=api_response.full_refresh_models,
            retries=api_response.retries,
            retry_delay=api_response.retry_delay,
            skip_data_tests=api_response.skip_data_tests,
        )

        # use dag timezone to convert execution_date
        self.execution_date = astimezone(self._execution_date, self.dag.timezone)

        self.node: ExecutorNode = init_dataclass_from_dict(ExecutorNode, api_response.model_dump(), dag=self.dag)
        self.node.variable = self.init_variables()

    def init_variables(self):
        variables = self.process_variables(
            self.node.variable,
            self.node.job_variable,
            self.execution_date,
            self.dag.schedule_interval,
            self.dag.timezone,
        )

        # set project id to environment variable
        os.environ[PROJECT_ID_KEY] = str(self.dag.project_id)
        # append airflow dag run conf to variables
        airflow_dag_run_conf = os.environ.get("RECURVE__JOB_RUN_CONF")
        if airflow_dag_run_conf:
            variables["job_run_conf"] = json.loads(airflow_dag_run_conf)

        return variables

    @classmethod
    def process_variables(
        cls,
        variables: dict,
        override_variables: dict,
        execution_date: str,
        schedule_interval: str,
        timezone: str | None = None,
    ) -> dict:
        """Process and merge variables from different sources with proper overrides.

        Args:
            variables: Base variables dict
            override_variables: Variables that should override base variables
            execution_date: Execution date string
            schedule_interval: Schedule interval string
            timezone: Optional timezone string, defaults to local timezone

        Returns:
            dict: Processed and merged variables

        The processing order is:
        1. Process normal variables first (in case they reference each other)
        2. Extract python code variables using processed normal variables
        3. Override with job variables last since they take precedence
        """
        valid_var_types = set(member.value for member in VariableType.__members__.values())
        timezone = timezone or tz_local

        def process_typed_value(val_type: str, val_value):
            processors = {
                "DATETIME": lambda x: astimezone(x, timezone),
                "DATE": lambda x: astimezone(x, timezone).date(),
                "JSON": json.loads,
            }
            return processors.get(val_type, lambda x: x)(val_value)

        # Split variables by type
        normal_vars = {}
        python_code_vars = {}

        for var_dict in (variables, override_variables):
            if not var_dict:
                continue

            for key, value in var_dict.items():
                var_value, var_type = value["value"], value["type"]

                if var_type == VariableType.PYTHON_CODE:
                    python_code_vars[key] = var_value
                elif var_type not in valid_var_types:
                    raise ValueError(f"Invalid variable type {var_type} for {key}")
                else:
                    normal_vars[key] = process_typed_value(var_type, var_value)

        # Process variables in order
        renderer = Renderer()
        processed_normal_vars = renderer.render_variables(normal_vars, execution_date, schedule_interval)

        job_vars = {}
        if override_variables:
            job_vars = {key: processed_normal_vars.get(key, value) for key, value in override_variables.items()}

        # Merge all variables with proper precedence
        final_vars = processed_normal_vars.copy()

        if python_code_vars:
            python_vars = cls._process_python_code_variable(
                python_code_vars, final_vars, execution_date, schedule_interval
            )
            final_vars.update(python_vars)

        final_vars.update(job_vars)  # Job variables take highest precedence

        return final_vars

    @classmethod
    def _process_python_code_variable(
        cls, python_code_variables: dict, new_variables: dict, execution_date: str, schedule_interval: str
    ) -> dict:
        r = Renderer()
        extracted_variables = {}
        for name, code in python_code_variables.items():
            if code is None:
                continue
            tmp_extracted_variables = r.extract_python_code_variable(
                python_code=code,
                exist_variables=new_variables,
                execution_date=execution_date,
                schedule_interval=schedule_interval,
            )
            extracted_variables.update(tmp_extracted_variables)
        return extracted_variables

    def run(self):
        if self.node.operator == "DBTOperator":
            self.run_impl()
            return
        with OutputInterceptor(handler=self._send_logs) as interceptor:
            setup_log_handler(interceptor)
            self.run_impl()

    def run_impl(self):
        logger.info(f"Recurve Executor start run {self.job_id}.{self.node_id}, {self.node.operator}")
        operator = self.init_operator()
        operator.execute()
        logger.info(f"Recurve Executor finish run {self.job_id}.{self.node_id}, {self.node.operator}")

    def _send_logs(self, message: str):
        self.client.send_back_logs(TaskLogRecord.init(self.job_id, logs=[message]))

    @staticmethod
    def _get_hostname():
        return socket.gethostname()

    @staticmethod
    def _get_pid() -> int:
        return os.getpid()

    def set_link_settings(self, link_workflow_id: int = None, link_node_id: int = None, is_link_workflow: bool = False):
        self.node.link_settings = {
            "workflow_id": link_workflow_id,
            "node_id": link_node_id,
            "is_link_workflow": is_link_workflow,
        }

    def init_operator(self) -> "BaseOperator":
        op_cls = get_operator_class(self.node.operator)
        operator = op_cls(self.dag, self.node, self.execution_date, variables=self.node.variable)
        self.set_operator_execution_date(operator)
        return operator

    def set_operator_execution_date(self, operator: "BaseOperator"):
        if "execution_date" not in self.node.variable:
            return
        new_execution_date = astimezone(self.node.variable["execution_date"], self.dag.timezone)
        operator.set_execution_date(new_execution_date)
