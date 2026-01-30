import logging

from airflow.exceptions import AirflowSkipException
from airflow.models import TaskInstance
from airflow.operators.bash import BashOperator
from airflow.utils.context import Context
from airflow.utils.task_instance_session import get_current_task_instance_session
from sqlalchemy.orm.attributes import flag_modified

from recurvedata.executors.utils import read_meta_file

logger = logging.getLogger(__name__)


class RecurveBashOperator(BashOperator):
    def execute(self, context: Context):
        try:
            res = super().execute(context)
            self.update_meta_to_task_instance_executor_config(context)
            return res
        except Exception:
            self.update_meta_to_task_instance_executor_config(context)
            raise

    @staticmethod
    def read_meta_file(context: Context) -> dict:
        return read_meta_file(
            context["dag"].dag_id, context["ti"].task_id, context["next_execution_date"] or context["execution_date"]
        )

    def update_meta_to_task_instance_executor_config(self, context: Context):
        meta = self.read_meta_file(context)
        if not meta:
            return
        logger.debug(f"update_meta_to_task_instance_executor_config: {str(meta)}")
        session = get_current_task_instance_session()
        task_instance = TaskInstance.get_task_instance(
            dag_id=context["dag"].dag_id,
            task_id=context["ti"].task_id,
            run_id=context["dag_run"].run_id,
            map_index=-1,
            session=session,
        )
        if task_instance:
            task_instance.executor_config.update(meta)
            flag_modified(task_instance, "executor_config")


class SkipSelfBashOperator(BashOperator):
    ui_color = "#e8f7e4"

    def execute(self, context):
        raise AirflowSkipException("This task is skipped")


class LinkNodeBashOperator(RecurveBashOperator):
    ui_color = "#8DEEEE"


class LinkErrorBashOperator(BashOperator):
    ui_color = "red"  # not used
