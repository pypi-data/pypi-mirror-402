import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from recurvedata.core.translation import _l
from recurvedata.dbt.utils import parse_run_model_log
from recurvedata.exceptions import MaxRetriesExceededException
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.task import BaseTask
from recurvedata.utils.date_time import utcnow_aware
from recurvedata.utils.helpers import get_environment_variable

if TYPE_CHECKING:
    from recurvedata.dbt.consts import DbtMaterialization
    from recurvedata.dbt.schemas import PreviewResult
    from recurvedata.dbt.service import DbtService

    try:
        from dbt.cli.main import dbtRunnerResult
    except ImportError:
        dbtRunnerResult = None

logger = logging.getLogger(__name__)


@dataclass
class TaskRuntimeException:
    exception: Exception

    def to_dict(self):
        return {
            "success": False,
            "exception": {
                "type": f"TaskRuntimeException-{type(self.exception).__name__}",
                "message": str(self.exception),
            },
        }


@dataclass
class DbtResultConstructor:
    project_id: int
    model_name: str
    materialization: "DbtMaterialization"
    compiled_code: str = None

    @staticmethod
    def _construct_timing(action_name: str, start_time: datetime.datetime, end_time: datetime.datetime) -> list[dict]:
        def _format_time(dt: datetime.datetime) -> str:
            dt_utc = dt.astimezone(datetime.timezone.utc)
            ds = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            return ds

        return [
            {"name": action_name, "started_at": _format_time(start_time), "completed_at": _format_time(end_time)},
        ]

    def construct_ephemeral_materialized_result(
        self, materialized_result_dct: dict, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> dict:
        """
        For ephemeral materialization, the materialized_result_dct $result.results is empty.
        CP relies on $result.results to show message and start/end time
        """
        if not materialized_result_dct["success"]:
            return materialized_result_dct
        result_dct = materialized_result_dct["result"]
        if not result_dct:
            return materialized_result_dct
        sub_results: list[dict] = result_dct["results"]
        if not sub_results:
            result_dct["results"] = [
                {
                    "unique_id": self.format_model_unique_id(),
                    "status": "success",
                    "timing": self._construct_timing("execute", start_time=start_time, end_time=end_time),
                    "message": "Ephemeral model compiled successfully",
                    "compiled_code": self.compiled_code,
                }
            ]
        return materialized_result_dct

    def format_model_unique_id(self) -> str:
        return f"model.project_{self.project_id}.{self.model_name}"


class DbtTask(BaseTask):
    def execute_impl(self):
        from recurvedata.dbt.schemas import PreviewResult
        from recurvedata.dbt.service import DbtService
        from recurvedata.dbt.utils import format_var
        from recurvedata.utils.redis_lock import RedisLock

        model_name = self.rendered_config.get("model_name") or self.rendered_config.get("entity_name")

        lock = RedisLock(
            f"dbt_task_{self.dag.project_id}_{model_name}", auto_extend=True, expire=60, timeout=60 * 60 * 1
        )
        lock.acquire()

        try:
            service = DbtService(self.dag.project_id)
            service.prepare()
            model_id: int = int(self.rendered_config["entity_id"])
            var_str = format_var(service, self.get_template_context())

            materialize_start_time = utcnow_aware()
            full_refresh = self.dag.full_refresh_models

            model_run_result = service.run_model(model_name, var_str, full_refresh=full_refresh, include_run_log=True)
            compiled_code = model_run_result.compiled_sql
            materialized_result = model_run_result.result
            run_sql = model_run_result.run_sql
            run_log = model_run_result.run_log

            materialize_end_time = utcnow_aware()

            if not compiled_code:
                logger.info("compiled_code empty, use un-compiled sql")
                compiled_code = service.read_model_sql(model_name)

            if not compiled_code:
                logger.info("compiled_code still empty, set materialized_result to failed")
                materialized_result.success = False
                materialized_result.exception = RuntimeError("Materialization failed due to empty compiled_code")
                materialized_result.result = None

            if not materialized_result.success:
                self.send_dbt_model_result(
                    service,
                    compiled_sql=compiled_code,
                    run_sql=run_sql,
                    run_log=run_log,
                    try_number=get_environment_variable("AIRFLOW_RETRY_NUMBER", int),
                    materialized_result=materialized_result,
                    materialize_start_time=materialize_start_time,
                    materialize_end_time=materialize_end_time,
                )
                raise Exception(f"run model {model_name} materialized failed")

            test_case_skipped = False
            if self.dag.skip_data_tests:
                logger.info("skip data tests")
                test_result = None
                test_case_sample_result = None
                test_case_skipped = True
            else:
                logger.info("run data tests")
                test_result = service.run_test(model_id, var_str)
                test_case_sample_result: dict[str, PreviewResult] = service.run_test_sample_data(test_result)
            self.send_dbt_model_result(
                service,
                compiled_sql=compiled_code,
                run_sql=run_sql,
                run_log=run_log,
                try_number=get_environment_variable("AIRFLOW_RETRY_NUMBER", int),
                materialized_result=materialized_result,
                test_case_result=test_result,
                test_case_sample_result=test_case_sample_result,
                materialize_start_time=materialize_start_time,
                materialize_end_time=materialize_end_time,
                test_case_skipped=test_case_skipped,
            )

            test_case_result_dct = self.format_test_case_result(test_result)
            if test_case_result_dct and not test_case_result_dct["success"]:
                raise Exception("Task Run failed due to Error / Failed test cases")
        except Exception as e:
            raise e from None
        finally:
            lock.release()

    @staticmethod
    def format_materialized_result(
        project_id: int,
        model_name: str,
        materialization: Union["DbtMaterialization", str],
        compiled_code: str,
        materialized_result: Union["dbtRunnerResult", "TaskRuntimeException"],
        materialize_start_time: datetime.datetime = None,
        materialize_end_time: datetime.datetime = None,
    ) -> dict | None:
        """
        materialized: model, ephemeral, view, incremental
        """
        from recurvedata.dbt.consts import DbtMaterialization
        from recurvedata.dbt.utils import dbt_runner_result_to_dict

        if not materialized_result:
            return
        if isinstance(materialized_result, TaskRuntimeException):
            materialized_result_dct = materialized_result.to_dict()
        else:
            materialized_result_dct = dbt_runner_result_to_dict(materialized_result)

        if materialization == DbtMaterialization.EPHEMERAL:
            constructor = DbtResultConstructor(
                project_id=project_id,
                model_name=model_name,
                materialization=materialization,
                compiled_code=compiled_code,
            )
            materialized_result_dct = constructor.construct_ephemeral_materialized_result(
                materialized_result_dct, materialize_start_time, materialize_end_time
            )

        if materialized_result_dct["success"]:
            results = materialized_result_dct.get("result", {}).get("results")
            if not results:
                # The selection criterion '' does not match any nodes
                materialized_result_dct["success"] = False

        return materialized_result_dct

    @staticmethod
    def format_test_case_result(test_case_result: Union["dbtRunnerResult", "TaskRuntimeException"]) -> dict | None:
        from recurvedata.dbt.utils import dbt_runner_result_to_dict

        if not test_case_result:
            return
        if isinstance(test_case_result, TaskRuntimeException):
            test_case_result_dct = test_case_result.to_dict()
        else:
            test_case_result_dct = dbt_runner_result_to_dict(test_case_result)
        return test_case_result_dct

    @property
    def model_name(self) -> str:
        return self.rendered_config.get("model_name") or self.rendered_config.get("entity_name")

    @property
    def materialization(self) -> str:
        return self.rendered_config.get("materialized")

    def send_dbt_model_result(
        self,
        service: "DbtService",
        compiled_sql: str | None,
        try_number: int,
        run_sql: str | None = None,
        run_log: str | None = None,
        materialized_result: Union["dbtRunnerResult", "TaskRuntimeException"] = None,
        test_case_result: Union["dbtRunnerResult", "TaskRuntimeException"] = None,
        test_case_sample_result: dict[str, "PreviewResult"] = None,
        materialize_start_time: datetime.datetime = None,
        materialize_end_time: datetime.datetime = None,
        test_case_skipped: bool = False,
    ):
        materialized_result_dct = self.format_materialized_result(
            self.dag.project_id,
            self.model_name,
            self.materialization,
            compiled_sql,
            materialized_result,
            materialize_start_time,
            materialize_end_time,
        )
        test_case_result_dct = self.format_test_case_result(test_case_result)

        if not compiled_sql:
            logger.info(f"compiled_sql empty, materialized_result_dct: {materialized_result_dct}")

        if test_case_sample_result:
            test_case_sample_result_dct = {
                unique_id: preview_obj.model_dump() for unique_id, preview_obj in test_case_sample_result.items()
            }
        else:
            test_case_sample_result_dct = None

        run_sql_log = parse_run_model_log(run_log)

        logger.info(f"debug: compiled sql: {compiled_sql}")
        logger.info(f"debug: run sql: {run_sql}")
        logger.info(f"debug: run_log: {run_log}")
        logger.info(f"debug: run_sql_log: {run_sql_log}")
        logger.info(f"debug: materialized_result_dct: {materialized_result_dct}")
        logger.info(f"debug: test_case_result_dct: {test_case_result_dct}")
        logger.info(f"debug: test_case_sample_result_dct: {test_case_sample_result_dct}")

        try:
            service.client.send_dbt_model_result(
                self.dag.id,
                self.node.node_key,
                compiled_sql,
                run_sql,
                run_sql_log=run_sql_log,
                raw_materialized_result=materialized_result_dct,
                raw_test_result=test_case_result_dct,
                test_case_sample_data=test_case_sample_result_dct,
                materialization=self.materialization,
                try_number=try_number,
                test_case_skipped=test_case_skipped,
            )
        except MaxRetriesExceededException as e:
            logger.exception(f"send_dbt_model_result failed, error: {e}")
        self.sent_dbt_model_result = True

    def on_execute_impl_error(self, err: Exception):
        from recurvedata.dbt.service import DbtService

        if getattr(self, "sent_dbt_model_result", False):
            return
        service = DbtService(self.dag.project_id)
        self.send_dbt_model_result(
            service,
            compiled_sql=None,
            try_number=get_environment_variable("AIRFLOW_RETRY_NUMBER", int),
            materialized_result=TaskRuntimeException(err),
            test_case_result=None,
        )


class DBTOperator(BaseOperator):
    task_cls = DbtTask

    @classmethod
    def config_schema(cls) -> dict:
        return {
            "type": "object",
            "properties": {
                "entity_name": {
                    "type": "string",
                    "title": _l("Entity Name"),
                    "description": _l("Entity Name"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "materialized": {  # for front-end display
                    "type": "string",
                    "title": _l("Materialized"),
                    "default": "view",
                    "enum": ["table", "view", "incremental", "ephemeral"],
                    "enumNames": ["table", "view", "incremental", "ephemeral"],
                },
            },
            "required": ["entity_name", "materialized"],
        }

    @classmethod
    def validate(cls, configuration) -> dict:
        return configuration

    @classmethod
    def ui_config_to_config(cls, configuration: dict) -> dict:
        source = configuration["source"]
        return source

    @classmethod
    def get_ds_name_field_values(cls, rendered_config: dict) -> list[str]:
        return []
