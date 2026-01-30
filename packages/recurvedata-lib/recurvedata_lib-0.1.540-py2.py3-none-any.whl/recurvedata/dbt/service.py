import contextlib
import io
import logging
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from recurvedata.core.templating import Renderer
from recurvedata.core.tracing import Tracing
from recurvedata.dbt.client import DbtClient
from recurvedata.dbt.consts import OVERWRITE_DIRECTORIES, OVERWRITE_FILES, DbtPath
from recurvedata.dbt.cosmos_utils import extract_graph
from recurvedata.dbt.error_codes import ERR
from recurvedata.dbt.schemas import CompileResult, DbtGraph, PreviewResult, RunModelResult
from recurvedata.dbt.utils import change_directory, format_var, run_deps_if_necessary
from recurvedata.exceptions import WrapRecurveException, wrap_error
from recurvedata.utils.compression import tar_gzip_uncompress
from recurvedata.utils.date_time import now
from recurvedata.utils.files import calculate_md5
from recurvedata.utils.helpers import get_env_id

tracer = Tracing()

if TYPE_CHECKING:
    from recurvedata.connectors.service import DataSourceWrapper
try:
    import yaml
    from dbt.cli.main import dbtRunnerResult
    from dbt.contracts.results import RunResult
except ImportError:
    dbtRunnerResult = RunResult = None

logger = logging.getLogger(__name__)


@dataclass
class DbtService:
    project_id: int
    project_connection_name: str = None
    force_regenerate_dir: bool = False
    ds: "DataSourceWrapper" = None
    need_fetch_variable: bool = False  # when compile/preview, need fetch variable
    variables: dict = None  # used in compile/preview

    @cached_property
    def client(self):
        return DbtClient()

    @cached_property
    def path(self):
        return DbtPath(project_id=self.project_id, env_id=get_env_id())

    @wrap_error(ERR.DP_FETCH_PROJECT_FAILED)
    @tracer.create_span()
    def fetch_project(self):
        def _is_the_same_file(file1: str, file2: str) -> bool:
            def __read_file(filename: str) -> bytes:
                with open(filename, "rb") as f:
                    return f.read()

            if os.path.exists(file1) != os.path.exists(file2):
                return False

            return __read_file(file1) == __read_file(file2)

        def _overwrite_from_gzip_dir(src_dir: str, dst_dir: str):
            for sub_dir in OVERWRITE_DIRECTORIES:
                src_sub_dir = os.path.join(src_dir, sub_dir)
                for root, dirs, files in os.walk(src_sub_dir):
                    dst_root = os.path.join(dst_dir, sub_dir, os.path.relpath(root, src_sub_dir))
                    os.makedirs(dst_root, exist_ok=True)
                    for tmp_file in files:
                        src_file = os.path.join(root, tmp_file)
                        dst_file = os.path.join(dst_root, tmp_file)
                        if _is_the_same_file(src_file, dst_file):
                            logger.info(f"skip {dst_file}")
                            continue
                        shutil.copy2(src_file, dst_file)
                    for dst_file_dir in os.listdir(dst_root):
                        if dst_file_dir not in dirs + files:
                            dst_file_dir = os.path.join(dst_root, dst_file_dir)
                            logger.info(f"remove {dst_file_dir}")
                            if os.path.isdir(dst_file_dir):
                                shutil.rmtree(dst_file_dir, ignore_errors=True)
                            else:
                                try:
                                    os.remove(dst_file_dir)
                                except FileNotFoundError:
                                    pass
            for tmp_file in OVERWRITE_FILES:
                src_file = os.path.join(src_dir, tmp_file)
                dst_file = os.path.join(dst_dir, tmp_file)
                if _is_the_same_file(src_file, dst_file):
                    logger.info(f"skip {dst_file}")
                    continue
                shutil.copy2(src_file, dst_file)

        logger.info(f"fetch dbt project: {self.project_id} -> {self.path.project_dir}")

        os.makedirs(self.path.base_path, exist_ok=True)
        logger.info(f"fetch dbt project: preparing 1 - base_path: {self.path.base_path}")

        gzip_temp_dir: str = tempfile.mkdtemp(dir=self.path.base_path, prefix=f"_tmp_{self.path.simple_project_dir}")
        gzip_file = f"{gzip_temp_dir}.tar.gz"
        logger.info(
            f"fetch dbt project: preparing 2 - simple_project_dir: {self.path.simple_project_dir} - gzip_file: {gzip_file}"
        )

        local_md5 = ""
        if os.path.exists(self.path.project_dir):
            if os.path.isfile(self.path.project_gzip_file):
                # check if the project exists -> then cal MD5 of project_gzip_file = {self.project_dir}.tar.gz
                local_md5 = calculate_md5(self.path.project_gzip_file)
                logger.info(
                    f"fetch dbt project: preparing 3 - current project_gzip_file: {self.path.project_gzip_file}, local_md5: {local_md5}"
                )
            else:
                logger.info(
                    f"fetch dbt project: preparing 3 - current project_gzip_file: {self.path.project_gzip_file} not exists"
                )
        else:
            logger.info(f"fetch dbt project: preparing 3 - current project_dir: {self.path.project_dir} not exists")

        fetch_gzip_result = self.client.fetch_project_gzip(self.project_id, gzip_file, client_md5=local_md5)
        logger.info(f"fetch dbt project: fetching - fetch_gzip_result: {fetch_gzip_result}")

        if not fetch_gzip_result:
            logger.info("fetch dbt project: md5 is the same, skip fetch project")
            # delete unused empty temp dir
            shutil.rmtree(gzip_temp_dir, ignore_errors=True)
            return

        tar_gzip_uncompress(gzip_file, gzip_temp_dir)

        logger.info(f"uncompress {gzip_file} to {gzip_temp_dir} success")

        os.makedirs(self.path.project_dir, exist_ok=True)
        _overwrite_from_gzip_dir(gzip_temp_dir, self.path.project_dir)
        shutil.move(gzip_file, self.path.project_gzip_file)
        shutil.rmtree(gzip_temp_dir, ignore_errors=True)

    @wrap_error(ERR.DP_FETCH_CONNECTION_FAILED)
    def fetch_connection(self):
        from recurvedata.connectors.service import get_datasource_by_config

        logger.info("start fetch connection")
        con_item = self.client.get_connection(self.project_id)
        self.ds = get_datasource_by_config(
            con_item.type, config=con_item.data, database=con_item.database, schema=con_item.database_schema
        )
        self.ds.recurve_connector.set_env_when_get_dbt_connection()

    @wrap_error(ERR.DP_FETCH_CONNECTION_FAILED)
    def fetch_connection_and_variables(self):
        from recurvedata.connectors.service import get_datasource_by_config

        logger.info("start fetch connection and variables")
        item = self.client.get_connection_and_variables(self.project_id)
        con_item = item.connection
        logger.info("after fetch connection and variables")
        self.ds = get_datasource_by_config(
            con_item.type, config=con_item.data, database=con_item.database, schema=con_item.database_schema
        )
        os.environ["DBT_USER"] = self.ds.user or ""
        os.environ["DBT_PASSWORD"] = self.ds.password or ""
        self.variables = self.prepare_variables(item.variables)
        logger.info("start process variables")
        logger.info("after process variables")

    def prepare_variables(self, variables: dict | None) -> dict:
        from recurvedata.executors.executor import Executor

        execution_date, schedule_interval = now(), "@daily"
        processed_variables = Executor.process_variables(variables or {}, {}, execution_date, schedule_interval)
        result_variables = Renderer().init_context(execution_date, schedule_interval)
        result_variables.update(processed_variables)
        return result_variables

    @tracer.create_span()
    def compile(self, model_name: str = None, inline_sql: str = None, validate_sql: bool = False) -> CompileResult:
        logger.info(f"prepare to compile: model_name: {model_name}, inline_sql: {inline_sql}")
        self.prepare()
        compiled_sql = self._run_compile(model_name, inline_sql)
        logger.info(f"compiled_sql is :{compiled_sql}")
        if validate_sql:
            self._run_preview(compiled_sql, limit=0)
        return CompileResult(compiled_sql=compiled_sql)

    def should_fetch_project(self) -> bool:
        if self.force_regenerate_dir or not os.path.exists(self.path.project_dir):
            return True
        remote_md5 = self.client.fetch_project_gzip_md5(self.project_id).md5
        local_md5 = calculate_md5(self.path.project_gzip_file)
        if remote_md5 == local_md5:
            logger.info("md5 is the same, skip fetch project")
            return False
        logger.info(f"remote_md5 md5 {remote_md5} vs local md5 {local_md5}")
        return True

    @tracer.create_span()
    def prepare(self):
        self.fetch_project()

        if self.need_fetch_variable:
            try:
                self.fetch_connection_and_variables()
            except Exception:  # back compatible
                logger.exception("fetch_connection_and_variables fail")
                self.fetch_connection()
        else:
            self.fetch_connection()

        self.run_dependency()

    @wrap_error(ERR.DEPS_FAILED)
    @tracer.create_span()
    def run_dependency(self):
        run_deps_if_necessary(self.path.project_dir)

    @wrap_error(ERR.MODEL_COMPILE_FAILED)
    @tracer.create_span()
    def _run_compile(self, model_name: str = None, inline_sql: str = None) -> str:
        if model_name:
            cmds = ["compile", "--select", model_name]
        elif inline_sql:
            cmds = ["compile", "-d", "--inline", inline_sql]
        else:
            raise ValueError("model_name or inline_sql must be specified")

        if self.variables:
            dbt_vars = format_var(self, self.variables)
            cmds += ["--vars", dbt_vars]

        result, _ = self._run_dbt_cmds(cmds)
        if result.success:
            compiled_code = result.result.results[0].node.compiled_code
            return compiled_code.strip()

    def _run_dbt_cmds(self, cmds: list, raise_when_failed: bool = True) -> ("dbtRunnerResult", str):
        from dbt.cli.main import dbtRunner

        logger.info(f"prepare run dbt cmds: {cmds}")
        dbt = dbtRunner()

        with change_directory(self.path.project_dir):
            log_buffer = io.StringIO()
            # Redirect stdout and stderr to the buffer
            with contextlib.redirect_stdout(log_buffer), contextlib.redirect_stderr(log_buffer):
                result: "dbtRunnerResult" = dbt.invoke(cmds)

            if raise_when_failed and not result.success:
                if isinstance(result.exception, BaseException):
                    raise result.exception
                raise ValueError(str(result.exception))
            logger.info(f"run dbt cmds finished: {cmds}")
            return result, log_buffer.getvalue()

    @tracer.create_span()
    def preview(
        self,
        model_name: str = None,
        inline_sql: str = None,
        limit: int = 100,
        no_data: bool = False,
        is_compiled: bool = False,
    ) -> "PreviewResult":
        self.prepare()

        if is_compiled:
            compiled_sql = inline_sql
            logger.info(f"sql is compiled: {compiled_sql}")
        else:
            compiled_sql = self._run_compile(model_name, inline_sql)
            logger.info(f"compiled_sql is :{compiled_sql}")

        if no_data:
            limit = 0
        return self._run_preview(compiled_sql, limit)

    @wrap_error(ERR.MODEL_PREVIEW_FAILED)
    def _run_preview(self, compiled_sql: str, limit: int = 100) -> "PreviewResult":
        from recurvedata.executors.cli.connector import ConnectionService
        from recurvedata.utils.sql import extract_order_by_from_sql

        # Extract ORDER BY from SQL to ensure it takes effect in the outer query
        recurve_con = self.ds.recurve_connector
        dialect = recurve_con.get_dialect() if hasattr(recurve_con, "get_dialect") else None
        orders = extract_order_by_from_sql(compiled_sql, dialect)

        con_service = ConnectionService()
        try:
            return con_service.preview_sql(self.ds, compiled_sql, limit, orders=orders)
        except Exception as e:
            raise WrapRecurveException(ERR.MODEL_PREVIEW_FAILED, e, data={"compiled_sql": compiled_sql})

    def get_test_cases(self, model_name: str) -> list[str]:
        cmds = ["ls", "--resource-type", "test", "--select", model_name]
        result, _ = self._run_dbt_cmds(cmds)
        if result.success:
            return result.result

    @wrap_error(ERR.MODEL_RUN_FAILED)
    @tracer.create_span()
    def _run_model(
        self, model_name: str, dbt_vars: str = None, full_refresh: bool = False
    ) -> tuple[str, "dbtRunnerResult"]:
        run_model_result = self.run_model(model_name, dbt_vars, full_refresh)
        compiled_sql = run_model_result.compiled_sql
        res = run_model_result.result
        if not res.success:
            error_message = None
            if res.result and res.result.results:
                # Case 1: Has results with error messages
                errors = [r.message for r in res.result.results if r.message]
                if errors:
                    error_message = "\n".join(errors)
            elif res.exception:
                # Case 2: Has exception
                error_message = str(res.exception)
            else:
                # Case 3: No results and no exception
                error_message = "Unknown error occurred during model run"

            raise WrapRecurveException(
                ERR.MODEL_RUN_FAILED,
                Exception(error_message),
                data={
                    "compiled_sql": compiled_sql,
                },
            )
        return compiled_sql, res

    @tracer.create_span()
    def run_model(
        self, model_name: str, dbt_vars: str = None, full_refresh: bool = False, include_run_log: bool = False
    ) -> RunModelResult:
        cmds = ["run", "--select", model_name]
        if dbt_vars:
            cmds.extend(["--vars", dbt_vars])
        if full_refresh:
            cmds.append("--full-refresh")

        if include_run_log:
            cmds.append("--debug")
            cmds.extend(["--log-format", "json"])

        res, run_log = self._run_dbt_cmds(cmds, raise_when_failed=False)

        compiled_code = self._extract_compiled_code(model_name, res)
        run_sql = self._get_model_run_sql(model_name)
        return RunModelResult(compiled_sql=compiled_code, result=res, run_sql=run_sql, run_log=run_log)

    def _extract_compiled_code(self, model_name: str, materialized_result: "dbtRunnerResult") -> str | None:
        # partial-compile will not have compiled_sql in materialized_result
        return self._extract_compiled_code_from_run_result(materialized_result) or self._get_model_compiled_sql(
            model_name
        )

    @classmethod
    def _extract_compiled_code_from_run_result(cls, materialized_result: "dbtRunnerResult") -> str | None:
        if not materialized_result.result:
            return
        results = materialized_result.result.results
        run_result: "RunResult" = results[0]
        compiled_code = run_result.node.compiled_code
        if compiled_code:
            return compiled_code.strip()

        return None

    def _get_model_compiled_sql(self, model_name: str) -> str | None:
        compiled_sql_path = Path(self.path.get_model_compiled_sql_path(model_name))
        if compiled_sql_path.exists():
            return compiled_sql_path.read_text()

    def _get_model_run_sql(self, model_name: str) -> str | None:
        run_sql_path = Path(self.path.get_model_run_sql_path(model_name))
        if run_sql_path.exists():
            return run_sql_path.read_text()

    @tracer.create_span()
    def run_test(self, model_id: int, dbt_vars: str = None) -> "dbtRunnerResult":
        cmds = [
            "test",
            "--select",
            f"tag:model_{model_id}",
        ]
        if dbt_vars:
            cmds.extend(["--vars", dbt_vars])

        res, _ = self._run_dbt_cmds(cmds, raise_when_failed=False)
        return res

    def extract_model_graph(self, models: list[str] = None, model_cmd: str = None) -> DbtGraph:
        """
        extract the models and model graph from model pipeline settings
        :param models: the models selected in the drop down list
        :param model_cmd: the command from the advanced mode
        """

        return extract_graph(self.path.project_dir, models, model_cmd)

    def extract_var_from_dbt_project(self) -> dict:
        with open(self.path.dbt_project_yml_path, "r") as file:
            dbt_project_dct = yaml.safe_load(file)
        return dbt_project_dct.get("vars", {})

    def read_model_sql(self, model_name: str) -> str | None:
        model_path = Path(self.path.get_model_sql_path(model_name))
        if not model_path.exists():
            return
        return model_path.read_text()

    @tracer.create_span()
    def run_test_sample_data(self, dbt_test_result: "dbtRunnerResult") -> dict[str, PreviewResult]:
        # todo: use dbt store-failure

        from recurvedata.executors.cli.connector import ConnectionService

        if not dbt_test_result.result:
            return {}

        result: dict[str, PreviewResult] = {}

        con_service = ConnectionService()

        def _run_single_test_case_sample_data(unique_id: str, sql: str):
            try:
                data: PreviewResult = con_service.preview_sql(self.ds, sql, limit=100)
            except Exception as e:
                logger.exception(f"run single test case {unique_id} fail: {e}, sql: {sql}")
                return
            result[unique_id] = data

        unique_id_2_sql = {
            dbt_result.node.unique_id: dbt_result.node.compiled_code
            for dbt_result in dbt_test_result.result.results
            if dbt_result.node.compiled_code
            # todo: if no failure, then skip fetching sample data
        }
        logger.debug(f"unique_id_2_sql: {unique_id_2_sql}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(_run_single_test_case_sample_data, unique_id, sql): unique_id
                for unique_id, sql in unique_id_2_sql.items()
            }

            for future in futures:
                future.result()

        return result
