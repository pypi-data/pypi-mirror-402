import copy
import datetime
import inspect
import json
import logging
import os
from functools import lru_cache, partial
from typing import Any, Callable, Generator, Union

import pendulum
from airflow.exceptions import AirflowSkipException
from airflow.models import DAG, BaseOperator, DagBag, DagRun, TaskInstance
from airflow.operators.empty import EmptyOperator
from airflow.operators.latest_only import LatestOnlyOperator
from airflow.operators.python import ShortCircuitOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.timetables.interval import CronDataIntervalTimetable
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.types import DagRunType
from slugify import slugify

from recurvedata.config import RECURVE_EXECUTOR_CLI, RECURVE_EXECUTOR_DBT_CLI
from recurvedata.consts import Operator
from recurvedata.schedulers.airflow_operators import LinkNodeBashOperator, RecurveBashOperator, SkipSelfBashOperator
from recurvedata.schedulers.base import DagSchema, SchedulerBase
from recurvedata.schedulers.consts import (
    DEFAULT_RETRY_DELAY,
    DEFAULT_RETRY_NUMBER,
    WORK_DIR,
    format_recurve_env_key,
    is_dev_run_job,
)
from recurvedata.schedulers.model import LinkNodeItem, LinkWorkflowItem, SchedulerNode
from recurvedata.schedulers.utils import format_dag_id
from recurvedata.utils.crontab import get_schedule
from recurvedata.utils.dataclass import init_dataclass_from_dict
from recurvedata.utils.date_time import ensure_datetime, now_aware
from recurvedata.utils.helpers import extract_dict

logger = logging.getLogger(__name__)


@lru_cache()
def _get_function_param_names(function: Callable) -> list[str]:
    sig = inspect.signature(function)
    return list(sig.parameters.keys())


def _on_finished_callback_static(callback_context):
    """Static callback function for DAG completion (success or failure).

    This function is designed to be serializable by avoiding instance references.
    It creates a new client instance to report job run results.
    """
    from recurvedata.schedulers.client import SchedulerClient

    dag_run: DagRun = callback_context["dag_run"]
    tis: list[TaskInstance] = dag_run.get_task_instances()
    task_info_map = {}
    for ti in tis:
        task_info_map[ti.task_id] = {
            "state": ti.state,
            "task_display_name": ti.task_display_name,
        }

    job_run_result = {
        "job_id": getattr(callback_context["dag"], "job_id", None),  # from Recurve metadata
        "run_id": callback_context["run_id"],
        "task_info_map": task_info_map,
        "state": dag_run.get_state(),
        "data_interval_end": dag_run.data_interval_end.isoformat(),
    }

    # Create a new client instance for this callback
    client = SchedulerClient()
    client.on_job_run_finished(job_run_result)


class SkipManualSensor(ExternalTaskSensor):
    def poke(self, context):
        if context["dag_run"].run_type == DagRunType.MANUAL:
            self.log.info("Manual trigger, skip sensor")
            raise AirflowSkipException("Manual trigger, skip waiting")
        return super().poke(context)


def fixed_execution_date_fn(own_dt: datetime.datetime, external_dag_id: str) -> datetime.datetime:
    dagbag = DagBag(read_dags_from_db=True)

    dag = dagbag.get_dag(external_dag_id)
    if dag is None:
        # external_dag_id not found, return own_dt
        return own_dt
    timetable = dag.timetable
    if isinstance(timetable, CronDataIntervalTimetable):
        external_prev_dt = timetable._get_prev(own_dt)
        if external_prev_dt is not None:
            return external_prev_dt
    return own_dt


AIRFLOW_DAG_INIT_PARAMS = _get_function_param_names(DAG.__init__)


class AirflowScheduler(SchedulerBase):
    def __init__(self, sharding_size: int = 1, sharding_key: int = 0):
        """Initialize the Airflow scheduler.

        Args:
            sharding_size: Number of shards to split DAGs across
            sharding_key: Which shard this scheduler instance handles
        """
        logger.debug(f"Initializing AirflowScheduler with sharding_size={sharding_size}, sharding_key={sharding_key}")

        # Temporarily removed sharding key extraction from environment due to DAG leakage issues
        # job_id = self.extract_sharding_key_from_environment()
        # if job_id:
        #     logger.info(
        #         f"Switching sharding_size from {sharding_size} to {job_id}, sharding_key from {sharding_key} to 0"
        #     )
        #     sharding_size = job_id
        #     sharding_key = 0

        super().__init__(sharding_size, sharding_key)
        self.link_node_dict = {}
        self.link_workflow_dict = {}

    @staticmethod
    def extract_sharding_key_from_environment() -> int | None:
        """Extract sharding key from environment variables.

        When Airflow worker runs 'airflow task run {dag_id} {task_id}',
        the dag_id is written to environment variables which we can use
        to determine the sharding key.

        Returns:
            Extracted sharding key as integer if found, None otherwise
        """
        dag_id = os.environ.get("_AIRFLOW_PARSING_CONTEXT_DAG_ID")
        if not dag_id:
            job_id = os.environ.get("RECURVE_AUTOGEN_SINGLE_SHARDING_SIZE")
            return int(job_id) if job_id else None

        job_id = dag_id.rsplit(".")[-1]
        return int(job_id) if job_id.isdigit() else None

    def list_scheduler_dag(self) -> Generator[DagSchema, None, None]:
        """Get all DAG information from SDK that matches sharding criteria.

        Yields:
            DagSchema objects for each matching DAG
        """
        response = self.client.list_jobs(sharding_size=self.sharding_size, sharding_key=self.sharding_key)

        # Build link node dictionary
        self.link_node_dict = {
            node.node_id: init_dataclass_from_dict(LinkNodeItem, node.model_dump()) for node in response.link_nodes
        }

        # Process link workflows
        for workflow in response.link_workflows:
            workflow_item: LinkWorkflowItem = init_dataclass_from_dict(LinkWorkflowItem, workflow.model_dump())

            # Process link nodes within workflow
            processed_link_nodes = []
            for node_dict in workflow_item.link_nodes:
                node_item: LinkNodeItem = init_dataclass_from_dict(LinkNodeItem, node_dict)
                node_item.node_id = workflow_item.node_id
                node_item.link_wf_id = workflow_item.link_wf_id
                processed_link_nodes.append(node_item)

            workflow_item.link_nodes = processed_link_nodes
            self.link_workflow_dict[workflow.node_id] = workflow_item

        # Yield DAG schemas
        for job in response.jobs:
            dag_schema: DagSchema = init_dataclass_from_dict(DagSchema, job.model_dump())
            yield dag_schema

    def execute(self) -> dict[str, DAG]:
        """Execute scheduler to create Airflow DAGs.

        Returns:
            Dictionary mapping DAG IDs to DAG objects
        """
        dag_dict = {}
        for dag_schema in self.list_scheduler_dag():
            airflow_dag = self.create_dag(dag_schema)
            if airflow_dag:
                dag_dict[airflow_dag.dag_id] = airflow_dag
        return dag_dict

    @staticmethod
    def dag_date_2_airflow_date(
        scheduler_interval: str, dag_date: Union[datetime.datetime], timezone: str, is_end_date: bool = False
    ) -> datetime.datetime:
        """Convert DAG date to Airflow date with timezone handling.

        Args:
            scheduler_interval: DAG schedule interval
            dag_date: Date to convert
            timezone: Target timezone
            is_end_date: Whether this is an end date requiring special handling

        Returns:
            Converted datetime with proper timezone
        """
        if not dag_date:
            return dag_date

        # Add timezone
        dag_date = ensure_datetime(dag_date).replace(tzinfo=pendulum.timezone(timezone))

        # Handle manual/once-off DAGs
        if scheduler_interval == "@once" or not scheduler_interval:
            return dag_date

        # Calculate execution dates
        next_execution_date = get_schedule(schedule_interval=scheduler_interval, dttm=dag_date, is_next=True)
        current_execution_date = get_schedule(
            schedule_interval=scheduler_interval, dttm=next_execution_date, is_next=False
        )

        if not is_end_date:
            if current_execution_date != dag_date:
                return current_execution_date

        previous_execution_date = get_schedule(
            schedule_interval=scheduler_interval, dttm=current_execution_date, is_next=False
        )
        return previous_execution_date

    @staticmethod
    def _cal_retry_number(dag_schema: DagSchema) -> int:
        """Calculate retry number for a DAG.

        Args:
            dag_schema: DAG schema to calculate retries for

        Returns:
            Number of retries to configure
        """
        if is_dev_run_job(dag_schema.name):
            return 0
        if dag_schema.retries is not None:
            return dag_schema.retries
        return DEFAULT_RETRY_NUMBER

    @staticmethod
    def _cal_retry_delay(dag_schema: DagSchema) -> datetime.timedelta:
        """Calculate retry delay for a DAG.

        Args:
            dag_schema: DAG schema to calculate retries for

        Returns:
            Retry delay to configure
        """
        return datetime.timedelta(seconds=3600)
        if dag_schema.retry_delay is not None:
            return datetime.timedelta(seconds=dag_schema.retry_delay)
        return datetime.timedelta(seconds=DEFAULT_RETRY_DELAY)

    def create_dag_impl(self, dag_schema: DagSchema) -> DAG | None:
        """Create Airflow DAG from schema.

        Args:
            dag_schema: Schema defining the DAG

        Returns:
            Created Airflow DAG object or None if creation fails
        """
        # Calculate dates
        airflow_end_date = self.dag_date_2_airflow_date(
            dag_schema.schedule_interval, dag_schema.end_date, dag_schema.timezone, is_end_date=True
        )

        airflow_start_date = (
            self.dag_date_2_airflow_date(dag_schema.schedule_interval, dag_schema.start_date, dag_schema.timezone)
            or now_aware()
        )

        # Set up default arguments
        default_args = {
            "owner": dag_schema.owner_username or self.DEFAULT_DAG_OWNER,
            "start_date": airflow_start_date,
            "end_date": airflow_end_date,
            "depends_on_past": False,
            "retries": self._cal_retry_number(dag_schema),
            "retry_delay": self._cal_retry_delay(dag_schema),
        }

        # Process Airflow-specific arguments
        airflow_args = dag_schema.scheduler_settings or {}
        if airflow_args:
            custom_defaults = airflow_args.pop("default_args", None)
            if custom_defaults:
                for key, value in custom_defaults.items():
                    if key in ("execution_timeout", "retry_delay"):
                        custom_defaults[key] = datetime.timedelta(seconds=value)
                    else:
                        custom_defaults[key] = value
                default_args.update(custom_defaults)

            # Remove reserved keys
            for reserved in ["dag_id", "default_args", "schedule_interval"]:
                airflow_args.pop(reserved, None)

        airflow_args = self._clean_airflow_args(airflow_args) or {}

        # Determine schedule interval
        schedule_interval = None if dag_schema.schedule_type == "manual" else dag_schema.schedule_interval

        # Create DAG
        dag = DAG(
            dag_id=self.format_dag_id(dag_schema),
            default_args=default_args,
            schedule=schedule_interval,
            start_date=airflow_start_date,
            end_date=airflow_end_date,
            dag_display_name=dag_schema.name,
            on_success_callback=_on_finished_callback_static,
            on_failure_callback=_on_finished_callback_static,
            **airflow_args,
        )

        # Add Recurve metadata
        dag._is_generated_by_recurve = True
        dag.job_id = dag_schema.job_id

        # Set up DAG structure
        self.setup_graph(dag, dag_schema)
        if dag_schema.enable_depends_on_jobs and dag_schema.depends_on_jobs:
            dag = self._inject_native_sensor_operator(dag, dag_schema.depends_on_jobs)

        return dag

    def setup_graph(self, dag: DAG, recurve_dag: DagSchema):
        """Set up the DAG graph structure.

        Args:
            dag: Airflow DAG to configure
            recurve_dag: Schema defining the DAG structure
        """
        operator_dict = {}

        # Create operators for each node
        for node_dict in recurve_dag.nodes:
            node: SchedulerNode = init_dataclass_from_dict(SchedulerNode, node_dict)
            node.id = int(node.id)

            try:
                operators = self.convert_node_to_operators(dag, recurve_dag, node)
            except Exception as exc:
                logger.exception(f"Failed to create node {dag.dag_id} {node.id}: {exc}")
                continue

            if not operators:
                continue

            # Add Recurve metadata to operators
            doc_metadata = {
                "recurve_node_id": node.id,
                "recurve_node_key": node.node_key,
            }

            for operator in operators:
                if isinstance(operator, TaskGroup):
                    for sub_op in operator:
                        sub_doc = json.loads(sub_op.doc_json) if sub_op.doc_json else {}
                        sub_doc.update(doc_metadata)
                        sub_op.doc_json = json.dumps(sub_doc)
                else:
                    operator.doc_json = json.dumps(doc_metadata)

            operator_dict[node_dict["node_key"]] = operators

        # Set up dependencies
        already_set = set()
        for upstream_key, downstream_key in recurve_dag.graph:
            edge = (upstream_key, downstream_key)
            if edge in already_set:
                continue

            if not (operator_dict.get(upstream_key) and operator_dict.get(downstream_key)):
                continue

            upstream = operator_dict[upstream_key][-1]
            downstream = operator_dict[downstream_key][0]
            upstream.set_downstream(downstream)
            already_set.add(edge)

    def convert_node_to_operators(self, dag: DAG, recurve_dag: DagSchema, node: SchedulerNode) -> list[BaseOperator]:
        """Convert a DAG node to Airflow operators.

        Args:
            dag: Parent Airflow DAG
            recurve_dag: Schema defining the DAG
            node: Node to convert

        Returns:
            List of created operators or None if conversion fails
        """
        # Prepare environment
        bash_env = self._prepare_bash_env(recurve_dag, node)
        kwargs = {
            "env": bash_env,
            "executor_config": {"workflow_version": recurve_dag.workflow_version},
        }

        # Handle link operators
        if Operator.is_link(node.operator):
            if node.id in self.link_workflow_dict:
                return self.convert_link_workflow_node_to_operators(dag, node, **kwargs)
            return self.convert_link_node_to_operators(dag, node, self.link_node_dict.get(node.id), **kwargs)

        # Get node-specific Airflow args
        node_airflow_args = self.get_node_airflow_args(node)
        kwargs.update(node_airflow_args)

        operators = []

        # Add latest-only operator if needed
        if dag.schedule_interval != "@once" and node.latest_only:
            task_id = self.format_task_id(node, "latest_only")
            latest_only = LatestOnlyOperator(task_id=task_id, dag=dag)
            operators.append(latest_only)

        # Add skip operator if needed
        if node.skip_downstream:
            skip_task = ShortCircuitOperator(
                dag=dag, task_id=self.format_task_id(node, "skip_downstream"), python_callable=lambda: False
            )
            operators.append(skip_task)

        # Add main operator
        task_id = self.format_task_id(node)
        main_operator = self._create_operator(dag, node, task_id, **kwargs)
        operators.append(main_operator)

        # Add empty node after skip_self operator to ensure proper trigger rule handling
        # Only add empty node if skip_downstream is False, to avoid conflicts
        if node.skip_self and not node.skip_downstream:
            empty_task_id = self.format_task_id(node, "skip_self")
            empty_operator = EmptyOperator(task_id=empty_task_id, trigger_rule=TriggerRule.NONE_FAILED, dag=dag)
            operators.append(empty_operator)

        # Set up dependencies
        for upstream, downstream in zip(operators[:-1], operators[1:]):
            upstream.set_downstream(downstream)

        return operators

    @staticmethod
    def _prepare_bash_env(recurve_dag: DagSchema, node: SchedulerNode) -> dict[str, Any]:
        """Prepare bash environment variables for operators.

        Args:
            recurve_dag: DAG schema
            node: Node to prepare environment for

        Returns:
            Dictionary of environment variables
        """
        env = {
            "AIRFLOW_RETRY_NUMBER": "{{ task_instance.try_number }}",
            "AIRFLOW_MAX_RETRY_NUMBER": "{{ task_instance.max_tries }}",
            "AIRFLOW_DATA_INTERVAL_END": "{{ task_instance.dag_run.data_interval_end.isoformat() }}",
            format_recurve_env_key("workflow_version"): recurve_dag.workflow_version,
            format_recurve_env_key("node_key"): node.node_key,
            format_recurve_env_key("job_run_conf"): "{{ dag_run.conf | tojson }}",
        }

        # Copy relevant environment variables
        for key, value in os.environ.items():
            if key.startswith("RECURVE__"):
                env[key] = value
            elif key.startswith("AIRFLOW__") and node.operator == "SensorOperator":
                env[key] = value
            elif key in (
                "AIRFLOW_CTX_DAG_RUN_ID",
                "AIRFLOW_CTX_TRY_NUMBER",
                "AIRFLOW_CTX_EXECUTION_DATE",
                "PATH",
                "PYENV_ROOT",
            ):
                env[key] = value

        return env

    def _create_operator(
        self, dag: DAG, node: SchedulerNode, task_id: str, stage: str = None, **kwargs
    ) -> BaseOperator:
        """Create an Airflow operator for a node.

        Args:
            dag: Parent Airflow DAG
            node: Node to create operator for
            task_id: ID for the task
            stage: Optional stage name
            **kwargs: Additional operator arguments

        Returns:
            Created operator
        """
        cmd = self.format_command(dag, node, stage)
        operator_class = SkipSelfBashOperator if node.skip_self else RecurveBashOperator

        return operator_class(task_id=task_id, bash_command=cmd, dag=dag, task_display_name=node.name, **kwargs)

    @staticmethod
    def format_command(dag: DAG, node: SchedulerNode, stage: str) -> str:
        """Format command string for bash operator.

        Args:
            dag: Parent Airflow DAG
            node: Node to create command for
            stage: Optional stage name

        Returns:
            Formatted command string
        """
        node_slug = f"{slugify(node.name)}.{node.id}"

        # Determine execution date template
        if dag.schedule_interval == "@once" or not dag.schedule_interval:
            execution_date = "logical_date"
        else:
            execution_date = "data_interval_end if data_interval_end is not none else logical_date"

        # Build command options
        options = [
            f"--dag_slug '{dag.dag_id}'",
            f"--node_slug '{node_slug}'",
            "--execution_date '{{ %s }}'" % execution_date,
        ]

        if stage is not None:
            options.append(f"--stage {stage}")

        # Build full command
        if node.operator == Operator.DBTOperator:
            return f'cd {WORK_DIR} && {RECURVE_EXECUTOR_DBT_CLI} execute {" ".join(options)}'
        return f'cd {WORK_DIR} && {RECURVE_EXECUTOR_CLI} execute {" ".join(options)}'

    @staticmethod
    def format_dag_id(row: DagSchema) -> str:
        """Format DAG ID from schema.

        Args:
            row: DAG schema

        Returns:
            Formatted DAG ID
        """
        return format_dag_id(row.job_id)

    @staticmethod
    def format_task_id(node: SchedulerNode, suffix=None) -> str:
        """Format task ID for a node.

        WARNING: This function should not be modified arbitrarily as it affects
        existing task IDs.

        Args:
            node: Node to format ID for
            suffix: Optional suffix to append

        Returns:
            Formatted task ID
        """
        task_id = f"{node.node_key}"
        if suffix:
            task_id = f"{task_id}-{suffix}"
        return task_id

    @staticmethod
    def format_link_node_task_id(node: SchedulerNode, suffix=None) -> str:
        """Format task ID for a link node.

        WARNING: This function should not be modified arbitrarily as it affects
        existing task IDs.

        Args:
            node: Node to format ID for
            suffix: Optional suffix to append

        Returns:
            Formatted task ID
        """
        task_id = f"{node.node_key}"
        if suffix:
            task_id = f"{task_id}-{suffix}"
        return task_id

    @staticmethod
    def get_node_airflow_args(node: SchedulerNode) -> dict:
        """Get Airflow arguments for a node.

        Args:
            node: Node to get arguments for

        Returns:
            Dictionary of Airflow arguments
        """
        scheduler_settings = node.scheduler_settings or {}

        # Get explicit Airflow args
        if "airflow_args" in scheduler_settings:
            airflow_args = json.loads(scheduler_settings["airflow_args"])
        else:
            airflow_args = {}

        # Process other Airflow settings
        for key, value in scheduler_settings.items():
            if key == "airflow_args" or not key.startswith("airflow"):
                continue

            key = key.lstrip("airflow_")

            # Convert time values to timedelta
            if key in ["execution_timeout", "retry_delay", "sla"] and isinstance(value, (int, float)):
                value = datetime.timedelta(seconds=value)

            airflow_args[key] = value

        return airflow_args

    @staticmethod
    def _clean_airflow_args(airflow_args: dict[str, Any] | None) -> dict[str, Any] | None:
        """Clean Airflow arguments to only include valid parameters.

        Args:
            airflow_args: Arguments to clean

        Returns:
            Cleaned arguments dictionary
        """
        if not airflow_args:
            return airflow_args
        return extract_dict(airflow_args, list(AIRFLOW_DAG_INIT_PARAMS))

    def __create_link_operator(
        self,
        dag: DAG,
        node: SchedulerNode,
        link_node: SchedulerNode,
        link_item: LinkNodeItem,
        task_id: str,
        stage: str = None,
        is_workflow: bool = False,
        **kwargs,
    ) -> LinkNodeBashOperator:
        """Create a link node operator.

        Args:
            dag: Parent Airflow DAG
            node: Parent node
            link_node: Link node to create operator for
            link_item: Link node details
            task_id: ID for the task
            stage: Optional stage name
            is_workflow: Whether this is part of a workflow
            **kwargs: Additional operator arguments

        Returns:
            Created link node operator
        """
        cmd = self.format_link_node_command(dag, node, link_item, stage, is_workflow)
        operator_class = SkipSelfBashOperator if link_node.skip_self else LinkNodeBashOperator

        return operator_class(
            task_id=task_id,
            bash_command=cmd,
            dag=dag,
            task_display_name=f"{node.name}.{link_item.link_node_name}",
            **kwargs,
        )

    @staticmethod
    def format_link_node_command(
        dag: DAG, node: SchedulerNode, link_detail: LinkNodeItem, stage: str, is_workflow: bool
    ) -> str:
        """Format command for link node operator.

        Args:
            dag: Parent Airflow DAG
            node: Parent node
            link_detail: Link node details
            stage: Optional stage name
            is_workflow: Whether this is part of a workflow

        Returns:
            Formatted command string
        """
        node_slug = f"{slugify(node.name)}.{node.id}"
        execution_date = "logical_date" if dag.schedule_interval == "@once" else "data_interval_end"

        # Build command options
        options = [
            f"--dag_slug '{dag.dag_id}'",
            f"--node_slug '{node_slug}'",
            "--execution_date '{{ %s }}'" % execution_date,
            f"--link_workflow_id {link_detail.link_wf_id}",
            f"--link_node_id {link_detail.link_node_id}",
        ]

        if stage is not None:
            options.append(f"--stage {stage}")

        if is_workflow:
            options.append("--is_link_workflow")

        # Build full command
        if link_detail.link_operator == Operator.DBTOperator:
            return f'cd {WORK_DIR} && {RECURVE_EXECUTOR_DBT_CLI} execute {" ".join(options)}'
        return f'cd {WORK_DIR} && {RECURVE_EXECUTOR_CLI} execute {" ".join(options)}'

    def convert_link_workflow_node_to_operators(self, dag: DAG, node: SchedulerNode, **kwargs) -> list[BaseOperator]:
        """Convert a link workflow node to operators.

        Args:
            dag: Parent Airflow DAG
            node: Node to convert
            **kwargs: Additional operator arguments

        Returns:
            List of created operators or None if conversion fails
        """
        link_workflow_item: LinkWorkflowItem = self.link_workflow_dict.get(node.id)
        if not link_workflow_item:
            return []

        operators = []

        # Add latest-only operator if needed
        if dag.schedule_interval != "@once" and node.latest_only:
            task_id = self.format_task_id(node, "latest_only")
            latest_only = LatestOnlyOperator(task_id=task_id, dag=dag)
            operators.append(latest_only)

        # Add skip operator if needed
        if node.skip_downstream:
            skip_task = ShortCircuitOperator(
                task_id=self.format_task_id(node, "skip_downstream"), python_callable=lambda: False, dag=dag
            )
            operators.append(skip_task)

        # Save original node properties
        node_original_name = node.name
        node_original_key = node.node_key

        has_inner_skip_downstream = False
        has_inner_latest_only = False
        link_end_task_id = self.format_task_id(node, "link_end")
        latest_only_task_id = self.format_task_id(node, "latest_only2")

        # Create task group
        group_id = f"{node.node_key}"
        with TaskGroup(group_id=group_id, dag=dag) as task_group:
            operator_dict = {}

            # Process each link node
            for link_item in link_workflow_item.link_nodes:
                link_plan_id = str(link_item.plan_id) if link_item.plan_id else dag.dag_id
                if link_plan_id != dag.dag_id:
                    logger.warning(
                        f"Link node {link_item.link_node_key} is not in the same plan as the current DAG, link_plan_id: {link_plan_id}, dag_id: {dag.dag_id}"
                    )
                    continue

                node.node_key = link_item.link_node_key

                # Prepare environment
                tmp_kwargs = copy.deepcopy(kwargs)
                tmp_env = tmp_kwargs.get("env", {})
                tmp_env.update(
                    {
                        format_recurve_env_key("link_workflow_version"): link_item.link_wf_version,
                        format_recurve_env_key("link_node_key"): link_item.link_node_key,
                        format_recurve_env_key("node_key"): f"{group_id}.{node.node_key}",
                    }
                )
                tmp_kwargs["env"] = tmp_env

                # Update executor config
                tmp_executor_config = kwargs.get("executor_config", {})
                tmp_executor_config.update(
                    {
                        "link_workflow_id": link_item.link_wf_id,
                        "link_workflow_version": link_item.link_wf_version,
                    }
                )
                tmp_kwargs["executor_config"] = tmp_executor_config

                # Create operators
                tmp_ops = self._convert_link_node_to_operators(
                    dag, node, link_item, is_workflow=True, workflow_skip_self=node.skip_self, **tmp_kwargs
                )
                operator_dict[link_item.link_node_key] = tmp_ops

                # Track special operators
                for op in tmp_ops:
                    if isinstance(op, ShortCircuitOperator):
                        has_inner_skip_downstream = True
                    if isinstance(op, LatestOnlyOperator):
                        has_inner_latest_only = True

            # Set up dependencies within group
            for upstream_key, downstream_key in link_workflow_item.link_graph:
                if not (operator_dict.get(upstream_key) and operator_dict.get(downstream_key)):
                    continue

                upstream = operator_dict[upstream_key][-1]
                downstream = operator_dict[downstream_key][0]
                upstream.set_downstream(downstream)

            operators.append(task_group)

        # Add end task if needed
        if (has_inner_skip_downstream or has_inner_latest_only) and not node.skip_downstream:
            operators.append(
                EmptyOperator(
                    task_id=link_end_task_id,
                    trigger_rule=TriggerRule.NONE_FAILED,
                    dag=dag,
                )
            )

            # Add second latest-only operator if needed
            if node.latest_only and has_inner_skip_downstream:
                latest_only2 = LatestOnlyOperator(task_id=latest_only_task_id, dag=dag)
                operators.append(latest_only2)

        # Set up dependencies between operators
        for upstream, downstream in zip(operators[:-1], operators[1:]):
            upstream.set_downstream(downstream)

        # Restore original node properties
        node.name = node_original_name
        node.node_key = node_original_key

        return operators

    def convert_link_node_to_operators(self, dag: DAG, node: SchedulerNode, link_item: LinkNodeItem, **kwargs) -> list:
        """Convert a link node to operators.

        Args:
            dag: Parent Airflow DAG
            node: Node to convert
            link_item: Link node details
            **kwargs: Additional operator arguments

        Returns:
            List of created operators
        """
        operators = []
        parent_node_key = node.node_key

        with TaskGroup(group_id=node.node_key, dag=dag) as task_group:
            node.node_key = link_item.link_node_key

            # Prepare environment
            tmp_kwargs = copy.deepcopy(kwargs)
            tmp_env = tmp_kwargs.get("env", {})
            tmp_env.update(
                {
                    format_recurve_env_key("link_workflow_version"): link_item.link_wf_version,
                    format_recurve_env_key("link_node_key"): link_item.link_node_key,
                    format_recurve_env_key("node_key"): f"{parent_node_key}.{link_item.link_node_key}",
                }
            )
            tmp_kwargs["env"] = tmp_env

            # Update executor config
            tmp_executor_config = tmp_kwargs.get("executor_config", {})
            tmp_executor_config.update(
                {
                    "link_workflow_id": link_item.link_wf_id,
                    "link_workflow_version": link_item.link_wf_version,
                }
            )
            tmp_kwargs["executor_config"] = tmp_executor_config

            self._convert_link_node_to_operators(dag, node, link_item, **tmp_kwargs)
            operators.append(task_group)

        return operators

    def _convert_link_node_to_operators(
        self,
        dag: DAG,
        node: SchedulerNode,
        link_item: LinkNodeItem,
        is_workflow: bool = False,
        workflow_skip_self: bool = False,
        **kwargs,
    ) -> list[BaseOperator]:
        """Internal helper to convert link node to operators.

        Creates a sequence of operators for a link node, handling latest-only checks,
        skip conditions, and the main link node operation.

        Args:
            dag: Parent Airflow DAG
            node: Node to convert
            link_item: Link node details
            is_workflow: Whether this is part of a workflow
            workflow_skip_self: Whether workflow has skip_self enabled
            **kwargs: Additional operator arguments

        Returns:
            List of created operators or None if conversion fails
        """
        operators = []
        # if not link_item:
        #     task_id = self.format_task_id(node)
        #     operators.append(None)  # TODO: Add fallback operator
        #     return operators

        # Determine node execution properties based on workflow context
        if not is_workflow:
            skip_downstream = node.skip_downstream
            latest_only = node.latest_only or link_item.link_latest_only
            skip_self = node.skip_self or link_item.link_skip_self or link_item.link_skip_downstream
        else:
            skip_downstream = link_item.link_skip_downstream
            latest_only = link_item.link_latest_only
            skip_self = link_item.link_skip_self or workflow_skip_self

        # Create link node with inherited properties
        link_node = SchedulerNode(
            operator=link_item.link_operator,
            node_key=link_item.link_node_key,
            name=link_item.link_node_name,
            id=link_item.link_node_id,
            scheduler_settings=link_item.link_scheduler_settings,
            skip_self=skip_self,
            skip_downstream=skip_downstream,
            latest_only=latest_only,
        )

        # Merge Airflow arguments from parent and link nodes
        parent_airflow_args = self.get_node_airflow_args(node)
        link_airflow_args = self.get_node_airflow_args(link_node)
        if parent_airflow_args:
            link_airflow_args.update(parent_airflow_args)
        kwargs.update(link_airflow_args)

        # Add latest-only check for scheduled DAGs
        if dag.schedule_interval != "@once" and link_node.latest_only:
            latest_only_task_id = self.format_task_id(node, "latest_only")
            latest_only_op = LatestOnlyOperator(task_id=latest_only_task_id, dag=dag)
            operators.append(latest_only_op)

        # Add skip operator if downstream tasks should be skipped
        if link_node.skip_downstream:
            skip_task_id = self.format_task_id(node, "skip_downstream")
            skip_args = {"ignore_downstream_trigger_rules": False} if is_workflow else {}

            skip_op = ShortCircuitOperator(task_id=skip_task_id, python_callable=lambda: False, dag=dag, **skip_args)
            operators.append(skip_op)

        # Create main link operator
        main_task_id = self.format_task_id(node)
        if Operator.is_link(link_node.operator):
            # Prevent nested link operators
            main_op = self.__create_link_operator(
                dag=dag,
                node=node,
                link_node=link_node,
                link_item=link_item,
                task_id=main_task_id,
                is_workflow=is_workflow,
            )
        else:
            # Add workflow metadata to executor config
            executor_config = copy.deepcopy(kwargs)
            executor_config["executor_config"].update(
                {
                    "link_workflow_id": link_item.link_wf_id,
                    "link_workflow_version": link_item.link_wf_version,
                }
            )

            main_op = self.__create_link_operator(
                dag=dag,
                node=node,
                link_node=link_node,
                link_item=link_item,
                task_id=main_task_id,
                is_workflow=is_workflow,
                **executor_config,
            )
        operators.append(main_op)

        # Add empty node after skip_self operator to ensure proper trigger rule handling
        # Only add empty node if skip_downstream is False, to avoid conflicts
        if link_node.skip_self and not link_node.skip_downstream:
            empty_task_id = self.format_task_id(node, "skip_self")
            empty_operator = EmptyOperator(task_id=empty_task_id, trigger_rule=TriggerRule.NONE_FAILED, dag=dag)
            operators.append(empty_operator)

        # Set up dependencies between operators
        for upstream_op, downstream_op in zip(operators[:-1], operators[1:]):
            upstream_op.set_downstream(downstream_op)

        return operators

    def _inject_native_sensor_operator(self, dag: DAG, depends_on_jobs: list[dict]) -> DAG:
        roots = dag.roots
        join = EmptyOperator(task_id="_injected_join", dag=dag, trigger_rule=TriggerRule.NONE_FAILED)
        sensors: list[ExternalTaskSensor] = []
        for dep_job in depends_on_jobs:
            for node_key in dep_job["node_key"]:
                sensor = SkipManualSensor(
                    task_id=f"_injected_wait__{dep_job['job_id']}__{node_key}",
                    external_dag_id=str(dep_job["job_id"]),
                    external_task_id=str(node_key),
                    execution_date_fn=partial(fixed_execution_date_fn, external_dag_id=str(dep_job["job_id"])),
                    execution_timeout=datetime.timedelta(seconds=dep_job["timeout"]),
                    soft_fail=False,
                    dag=dag,
                    retries=0,
                )
                sensors.append(sensor)

        for sensor in sensors:
            sensor.set_downstream(join)
        for root in roots:
            join.set_downstream(root)
        return dag


if __name__ == "__main__":
    scheduler = AirflowScheduler()
    globals().update(scheduler.execute())
