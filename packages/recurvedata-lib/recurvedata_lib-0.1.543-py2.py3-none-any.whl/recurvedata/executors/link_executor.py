"""
used in RecurveLinkNode
调用某个 node

"""

import datetime
import logging

from recurvedata.consts import Operator
from recurvedata.executors.client import ExecutorClient
from recurvedata.executors.executor import Executor
from recurvedata.executors.models import ExecutorDag, ExecutorNode
from recurvedata.executors.schemas import WorkflowNodeItem
from recurvedata.executors.utils import convert_var_value_from_string, get_variable_type_by_value, update_meta_file
from recurvedata.operators.task import BaseTask
from recurvedata.utils.dataclass import init_dataclass_from_dict

logger = logging.getLogger(__name__)


class LinkExecutor(Executor):
    """Executor for running linked workflow nodes.

    The LinkExecutor allows executing a node from another workflow by linking to it.
    It handles:

    - Executing a node from a different workflow while maintaining the original DAG context
    - Overriding task instance reporting to track the link relationship
    - Preserving the original DAG ID and node ID for file generation
    - Converting and passing custom variables between workflows
    - Supporting both single node and full workflow linking

    Args:
        origin_dag (ExecutorDag): The original DAG containing the link node
        origin_node (ExecutorNode): The original node that links to another workflow
        execution_date (datetime): Execution timestamp for the run
        link_workflow_id (int): ID of the workflow being linked to
        link_node_id (int): ID of the specific node being linked to
        link_workflow_name (str, optional): Name of the linked workflow
        link_node_name (str, optional): Name of the linked node
        link_node_key (str, optional): Key identifier for the linked node
        custom_variables (dict, optional): Variables to pass to the linked node
        is_link_workflow (bool, optional): Whether linking to a full workflow vs single node
    """

    def __init__(
        self,
        origin_dag: ExecutorDag,
        origin_node: ExecutorNode,
        execution_date: datetime.datetime,
        link_workflow_id: int,
        link_node_id: int,
        link_workflow_name: str = None,
        link_node_name: str = None,
        link_node_key: str = None,
        custom_variables: dict = None,
        is_link_workflow: bool = False,
    ):
        self.origin_dag = origin_dag
        self.origin_node = origin_node
        self.link_workflow_name = link_workflow_name
        self.link_node_name = link_node_name
        self.link_node_key = link_node_key
        self.link_workflow_id = link_workflow_id
        self.link_node_id = link_node_id
        self.custom_variables = custom_variables
        self.is_link_workflow = is_link_workflow

        # execution_date is passed from LinkOperator, which has been converted to origin_dag's timezone
        # self.execution_date = astimezone(execution_date, tz_local)
        self.execution_date = execution_date

        self.client: ExecutorClient = ExecutorClient()
        self.job_id = origin_dag.dag_id  # used in get_connection_by_name
        self.project_id = origin_dag.project_id

        self.dag: ExecutorDag = None
        self.node: ExecutorNode = None
        self.init_dag_node()
        self.register_context()

    def _init_task_instance_on_task_start(self, task: BaseTask):
        if self.is_link_workflow:  # todo: use scheduler?
            task_id = f"{self.origin_node.node_key}.{task.node.node_key}"
        else:
            task_id = f"{self.origin_node.node_key}"
        update_meta_file(
            self.origin_dag.id,
            task_id,
            task.execution_date,
            {
                "operator": Operator.LinkOperator,
                "task": "LinkTask",
                "link_operator": task.node.operator,
                "link_task": task.__class__.__name__,
                "link_workflow_id": self.link_workflow_id,
                "link_workflow_version": self.dag.workflow_version,
            },
        )

    def _prepare_task_end_payload(self) -> dict:
        payload = super()._prepare_task_end_payload()
        payload.update(
            {
                "link_node_id": self.link_node_id,
                "node_id": self.origin_node.id,
                "link_workflow_id": self.link_workflow_id,
            }
        )
        return payload

    def init_dag_node(self):
        """Initialize the DAG and Node objects for the linked workflow execution.

        Fetches workflow node data from API, creates ExecutorDag using origin DAG properties,
        initializes ExecutorNode, and sets up variables.
        """
        logger.info(f"Initializing DAG node for workflow {self.link_workflow_id}, node {self.link_node_id}")

        # Fetch workflow node data from API
        api_response: WorkflowNodeItem = self.client.get_workflow_node(self.link_workflow_id, self.link_node_id)

        # Create ExecutorDag using origin DAG properties
        self.dag: ExecutorDag = ExecutorDag(
            id=self.origin_dag.id,  # Use origin_dag id for TransferOp filename generation
            project_id=self.project_id,
            name=api_response.workflow_name,
            scheduler_type=self.origin_dag.scheduler_type,
            schedule_interval=self.origin_dag.schedule_interval,
            timezone=self.origin_dag.timezone,
            owner=self.origin_dag.owner,
            workflow_version=api_response.workflow_version,
        )

        # Initialize ExecutorNode from API response
        self.node: ExecutorNode = init_dataclass_from_dict(ExecutorNode, api_response.model_dump(), dag=self.dag)

        # Process and set variables
        self.custom_variables = self.process_custom_variable_type(self.custom_variables)
        self.node.job_variable = self.custom_variables
        self.node.variable = self.init_variables()

    def process_custom_variable_type(self, variables: dict) -> dict:
        """Process and convert custom variable types from string to their proper types.

        The frontend sends all variable values as strings, so we need to convert them to
        their proper types based on either:
        1. The variable type defined in the node's variables
        2. The inferred type from python code variables
        3. Keep original value if variable no longer exists in workflow

        Args:
            variables: Dictionary of variables to process

        Returns:
            Dictionary with variables converted to their proper types
        """
        if not variables:
            return variables

        new_variables = {}
        # Get current workflow variables to check types and python code vars
        workflow_vars = self.init_variables()

        for name, value in variables.items():
            # Check if variable exists in node variables
            if name in self.node.variable:
                val_type = self.node.variable[name]["type"]

            # Check if it's a python code variable
            elif name in workflow_vars:
                val_type = get_variable_type_by_value(workflow_vars[name])

            # Variable no longer exists in workflow, keep as-is
            else:
                new_variables[name] = value
                continue

            # Convert string value to proper type
            new_variables[name] = convert_var_value_from_string(val_type, value)

        return new_variables

    def run(self):
        logger.info(f"Recurve Link Executor start run {self.dag.name}.{self.node.name} {self.node.operator}")
        operator = self.init_operator()
        operator.execute()
        logger.info(f"Recurve Executor finish run {self.dag.name}.{self.node.name}, {self.node.operator}")
