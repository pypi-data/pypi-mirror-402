import datetime
import json
import logging
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from recurvedata.dbt.consts import (
    DbtFileNames,
    format_installed_packages_path,
    format_package_lock_path,
    format_packages_yml_path,
)
from recurvedata.utils.files import FileLock

try:
    import yaml
    from dbt.cli.main import dbtRunnerResult
    from dbt.contracts.results import RunExecutionResult, RunResultsArtifact
    from dbt.exceptions import DbtRuntimeError
except ImportError:
    dbtRunnerResult = None
    DbtRuntimeError = None
    RunExecutionResult = RunResultsArtifact = None

if TYPE_CHECKING:
    from recurvedata.dbt.service import DbtService

logger = logging.getLogger(__name__)


@contextmanager
def change_directory(new_dir):  # todo(chenjingmeng): use dbt api instead of cli
    """Context manager to change the current working directory temporarily."""
    original_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(original_dir)


def extract_project_name(project_yml: str) -> str:
    with open(project_yml, "r") as file:
        dbt_project = yaml.safe_load(file)
    project_name = dbt_project.get("name")
    return project_name


def run_dbt_cmds(project_dir: str, cmds: list) -> dbtRunnerResult:
    from dbt.cli.main import dbtRunner

    def _set_default_os_env():
        os.environ.setdefault("DBT_USER", "")
        os.environ.setdefault("DBT_PASSWORD", "")

    _set_default_os_env()
    dbt = dbtRunner()
    logger.info(f"prepare run dbt cmds: {cmds}")
    with change_directory(project_dir):
        result: dbtRunnerResult = dbt.invoke(cmds)
        return result


def dbt_runner_result_to_dict(result: dbtRunnerResult) -> dict:
    def _exception_to_dict(exception: DbtRuntimeError | BaseException | None) -> dict | None:
        if exception is None:
            return None
        if isinstance(exception, DbtRuntimeError):
            return exception.data()
        return {
            "type": type(exception).__name__,
            "message": str(exception),
        }

    def _result_to_dict(sub_result: RunExecutionResult | None) -> dict | None:
        if isinstance(sub_result, RunExecutionResult):
            res_dct = sub_result.to_dict(omit_none=False)
            return _format_cp_result_dct(res_dct)

    def _format_cp_result_dct(dbt_result_dct: dict) -> dict:
        if not dbt_result_dct.get("results"):
            return dbt_result_dct
        results: list[dict] = dbt_result_dct["results"]
        if results:
            for sub_result in results:
                node_dct = sub_result.get("node", {})
                sub_result.update(node_dct)  # on CP, DBTTestResultDetails needs node data like unique_id to validate
                # todo: better to adjust cp pydantic schema
        return dbt_result_dct

    return {
        "success": result.success,
        "exception": _exception_to_dict(result.exception),
        "result": _result_to_dict(result.result),
    }


class VariableJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        return self.format_var(obj)

    @classmethod
    def format_var(cls, value: Any):
        if value is None or isinstance(value, (int, bool, float)):
            return value
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        return str(value)


def format_var(service: "DbtService", variables: dict) -> str | None:
    default_var_dct: dict = service.extract_var_from_dbt_project()
    override_variables: dict = {
        k: v for (k, v) in variables.items() if k not in default_var_dct or v != default_var_dct[k]
    }
    if not override_variables:
        return
    vars_string = json.dumps(override_variables, cls=VariableJSONEncoder)
    return vars_string


def should_run_dependency(project_dir: str) -> bool:
    packages_yml = Path(format_packages_yml_path(project_dir))
    if not packages_yml.exists():
        return False
    if packages_yml.stat().st_size == 0:
        return False
    data: dict = read_yaml_file(str(packages_yml))
    if not data.get("packages"):
        return False
    package_lock = Path(format_package_lock_path(project_dir))
    if not package_lock.exists():
        return True
    packages_dir = Path(format_installed_packages_path(project_dir))
    if not packages_dir.exists():
        # maybe concurrency issue, causing the dbt_packages dir missing
        return True
    data: dict = read_yaml_file(str(package_lock))
    pack_cnt = len(data.get("packages", []))
    if pack_cnt > len(os.listdir(str(packages_dir))):
        # previous concurrency issue
        return True
    if packages_yml.stat().st_mtime > package_lock.stat().st_mtime:
        return True
    return False


def read_yaml_file(filename: str) -> dict:
    with open(filename, "r") as file:
        return yaml.safe_load(file)


def run_deps_if_necessary(project_dir: str):
    if not should_run_dependency(project_dir):
        logger.info(f"skip deps on {project_dir}")
        return

    lock = FileLock(lock_file_path=Path(project_dir).with_suffix(".deps_lock"))
    with lock:
        if not should_run_dependency(project_dir):
            logger.info(f"skip deps on {project_dir}")
            return
        res = run_dbt_cmds(
            project_dir,
            [
                "deps",
            ],
        )
        if not res.success:
            raise DbtRuntimeError(f"run deps failed on {project_dir}, {res.exception}")

        lock_file = Path(format_package_lock_path(project_dir))
        if lock_file.exists():
            lock_file.touch()  # used in should_run_dependency
    logger.info(f"deps on {project_dir} finish")


def ensure_manifest_json_exists(project_dir: str):
    manifest_path = Path(project_dir) / "target" / DbtFileNames.MANIFEST_FILE.value
    if manifest_path.exists():
        return
    run_dbt_cmds(project_dir, ["parse"])



def _has_error_log(log: dict) -> bool:
    log_data = log.get('data')
    if log_data:
        return log_data.get('status') == 'error' or 'error' in log_data.get("base_msg", "")
    return False


def _create_success_log(sql: str) -> dict:
    return {
        "sql": sql,
        "status": 'success'
    }


def _create_failed_log(sql: str) -> dict:
    return {
        "sql": sql,
        "status": 'failed'
    }

def parse_run_model_log(run_log: str) -> list[dict]:
    if not run_log:
        return []

    run_sql_log = []
    sql = None
    for line in run_log.splitlines():
        try:
            log = json.loads(line)
            log_data = log.get('data')

            if log_data and 'sql' in log_data:
                # If there is no error in the log instead we meet the next sql, the sql is success
                if sql is not None:
                    run_sql_log.append(_create_success_log(sql))

                sql = log_data['sql']
                # Remove /* ... */ using regex
                cleaned = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
                # Strip whitespace to get the SQL
                sql = cleaned.strip()

            elif sql:
                # failed if status is error or log has base_msg contains error keyword
                # if log does not have status or base_msg, then skip
                if _has_error_log(log):
                    run_sql_log.append(_create_failed_log(sql))
                    sql = None


        except json.JSONDecodeError:
            logger.error("Skipping non-JSON line:", line)

    # mark log success
    if sql is not None:
        run_sql_log.append(_create_success_log(sql))

    return run_sql_log