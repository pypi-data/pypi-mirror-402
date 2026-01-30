import logging
import os
from tempfile import NamedTemporaryFile

from recurvedata.core.translation import _l
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.task import BaseTask
from recurvedata.utils.mp import robust_run_subprocess

logger = logging.getLogger(__name__)

AIRFLOW_PYTHON_PATH = "python"  # system python path


class SensorTask(BaseTask):
    """
    Sensor operator is used to create a sensor that could check upstream task status,
    will wait until the upstream task is success.
    It uses airflow ExternalTaskSensor to check the status of the upstream task.
    For modeling pipeline,
        the node_key is the node_key of the selected model.
    for advanced pipeline,
        - if normal Operator like SQLOperator, the node_key is the node_key of the SQLOperator.
        - if Modeling Pipeline ( which is LinkModelPipelineOperator), the node_key is  "{node_key of the LinkModelPipelineOperator}.{node_key of the model}"

    """

    # todo: same schedule interval dependency

    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "title": _l("Project Name"),
                    "description": _l("Project Name containing the external task"),
                    "ui:field": "SensorOperatorProjectSelectField",
                },
                "job_id": {
                    "type": "string",
                    "title": _l("Job Name"),
                    "description": _l("Job Name of the external task"),
                    "ui:field": "SensorOperatorJobSelectField",
                },
                "node_key": {
                    "type": "string",
                    "title": _l("Node Name"),
                    "description": _l("Node Name of the external task"),
                    "ui:field": "SensorOperatorNodeSelectField",
                },
                "wait_time": {
                    "type": "integer",
                    "title": _l("Wait Time"),
                    "description": _l("Wait time in seconds between checks"),
                    "ui:options": {
                        "min": 0,
                        "step": 1,
                    },
                },
                "timeout": {
                    "type": "integer",
                    "title": _l("Timeout"),
                    "description": _l("Timeout"),
                    "default": 60,
                    "ui:options": {
                        "min": 0,
                        "step": 1,
                    },
                },
            },
            "required": ["project_id", "job_id", "node_key"],
        }

    def generate_airflow_operator_code(self):
        config = self.rendered_config
        external_job_id = config["job_id"]
        external_node_key = config["node_key"]
        execution_delta = config.get("wait_time", 0)
        timeout = config.get("timeout", 3600)
        dag_name = self.dag.name

        return f"""
import sys
from recurvedata.operators.sensor_operator.airflow_utils import format_external_dag_id, format_external_task_id, data_interval_end_to_data_interval_start
from airflow.sensors.external_task import ExternalTaskSensor
import datetime
import logging
from recurvedata.schedulers.consts import is_dev_run_job

logger = logging.getLogger()
external_dag_id = format_external_dag_id({external_job_id!r})
external_task_id = format_external_task_id({external_node_key!r})

external_dag = get_dag_from_db(external_dag_id)
if not external_dag:
    raise ValueError("External DAG not found")
external_task = external_dag.get_task(external_task_id)
if not external_task:
    raise ValueError("External Task not found")

data_interval_end = context["data_interval_end"]
external_data_interval_end = data_interval_end - datetime.timedelta(seconds={execution_delta})
external_data_interval_start = data_interval_end_to_data_interval_start(external_dag, external_data_interval_end)

logger.debug("external_data_interval_start " + str(external_data_interval_start))

tmp_task_id="tmp_task_id_for_external_task_sensor"
operator = ExternalTaskSensor(
        dag=dag,
        task_id=tmp_task_id,
        external_dag_id=external_dag_id,
        external_task_id=external_task_id,
        execution_date_fn = lambda *args, **kwargs: external_data_interval_start,
        execution_timeout = datetime.timedelta(seconds={timeout}),
    )
if is_dev_run_job({dag_name!r}):
    logger.info(f"dag_name: {dag_name!r}")
    logger.info(f"skip: SensorOperator is not working in dev mode")
    sys.exit(0)

"""

    def generate_airflow_code(self) -> str:
        config = self.rendered_config
        timeout = config.get("timeout", 3600)
        operator_code = self.generate_airflow_operator_code()
        return """
import os
import time
from recurvedata.operators.sensor_operator.airflow_utils import prepare_airflow_env, get_dag_from_db, \
build_execute_context
from recurvedata.utils.timeout import timeout

prepare_airflow_env()

dag_id = os.environ.get("AIRFLOW_CTX_DAG_ID")
task_id = os.environ.get("AIRFLOW_CTX_TASK_ID")
run_id = os.environ.get("AIRFLOW_CTX_DAG_RUN_ID")

dag = get_dag_from_db(dag_id)
task = dag.get_task(task_id)
context = build_execute_context(dag, task, run_id)

{operator_code}

with timeout({timeout}):
    operator.execute(context)
    """.format(
            operator_code=operator_code,
            timeout=timeout,
        )

    def __run_airflow_operator(self, filename: str):
        script_path = os.path.abspath(filename)
        env = os.environ.copy()
        output, ret_code = robust_run_subprocess([AIRFLOW_PYTHON_PATH, script_path], _logger=logger, env=env)
        if ret_code:
            raise RuntimeError(f"Airflow Error:\n{output}")

    def execute_impl(self, *args, **kwargs):
        code = self.generate_airflow_code()
        prefix = f"reorc_sensor_operator_{self.dag.id}_{self.node.id}_"
        with NamedTemporaryFile(mode="w+t", prefix=prefix, suffix=".py") as tmp_file:
            tmp_file.write(code)
            tmp_file.flush()
            self.__run_airflow_operator(tmp_file.name)


class SensorOperator(BaseOperator):
    task_cls = SensorTask
