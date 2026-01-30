import asyncio
import contextlib
import datetime
import logging
import os
import traceback
from typing import TYPE_CHECKING, Callable, Optional

import pendulum

from recurvedata.config import EXECUTOR_META_PATH
from recurvedata.error_codes import ERR
from recurvedata.exceptions import RecurveException, TimeoutException, WrapRecurveException
from recurvedata.executors.consts import VAR_CONVERT_STRING_FUNCS, VariableType
from recurvedata.utils import json_dumps, json_loads
from recurvedata.utils.timeout import timeout

if TYPE_CHECKING:
    from recurvedata.executors.schemas import ResponseModel


def convert_var_value_from_string(var_type, var_value):
    """
    the var value from front-end is in string type，
    this function will transform var value to corresponding type
    """
    if not isinstance(var_value, str):
        return var_value
    func = VAR_CONVERT_STRING_FUNCS[var_type]
    return func(var_value)


def get_variable_type_by_value(value):
    type_mappings = {
        bool: VariableType.BOOLEAN,
        int: VariableType.INT,
        float: VariableType.FLOAT,
        str: VariableType.STRING,
        dict: VariableType.STRING,  # 先用 STRING 类型（key 非 str 情况下，JSON 类型会报错）
        (datetime.datetime, datetime.date, pendulum.DateTime, pendulum.Date): VariableType.DATETIME,
    }
    for types, var_type in type_mappings.items():
        if isinstance(value, types):
            return var_type
    return VariableType.STRING


def format_meta_file_path(job_id: int, node_key: str, execution_date: datetime.datetime) -> str:
    sub_path = os.path.join(str(job_id), node_key, execution_date.isoformat())
    path = os.path.join(EXECUTOR_META_PATH, sub_path)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "meta.json")


def update_meta_file(job_id: int, node_key: str, execution_date: datetime.datetime, meta: dict):
    if not meta:
        return
    file_path = format_meta_file_path(job_id, node_key, execution_date)
    with open(file_path, "w") as f:
        f.write(json_dumps(meta))


def read_meta_file(
    job_id: int, node_key: str, execution_date: datetime.datetime, delete_after_read: bool = False
) -> Optional[dict]:
    file_path = format_meta_file_path(job_id, node_key, execution_date)
    if not os.path.exists(file_path):
        return
    with open(file_path, "r") as f:
        meta = json_loads(f.read())
    if delete_after_read:
        with contextlib.suppress(OSError, TypeError, ValueError):
            os.unlink(file_path)
    return meta


def get_airflow_run_id():
    return os.environ.get("AIRFLOW_CTX_DAG_RUN_ID")


def get_airflow_try_number():
    return os.environ.get("AIRFLOW_CTX_TRY_NUMBER")


def get_recurve_node_key():
    return os.environ.get("RECURVE__NODE_KEY")


def run_with_result_handling(func: Callable = None, ttl: int = None, result_filename: str = None, *args, **kwargs):
    """Run a function with timeout and handle the result.

    Args:
        func:
        ttl (int, optional): timeout in seconds.
        result_filename: the file to dump the result.
    """
    from recurvedata.executors.schemas import ResponseError, ResponseModel

    def exec_with_timeout(ttl: int):
        with timeout(ttl):
            return func(*args, **kwargs)

    result = ResponseModel(ok=True)
    try:
        data = exec_with_timeout(ttl) if ttl else func(*args, **kwargs)
        result.data = data
    except Exception as e:
        result.ok = False
        if not isinstance(e, RecurveException):
            e = WrapRecurveException(ERR.UNKNOWN_ERROR, e)
        result.error = ResponseError.from_recurve_exception(e)

    if result_filename:
        result.model_dump_json_file(result_filename)
    else:
        logging.info(result.model_dump_json(indent=2))
        return result


async def run_with_result_handling_v2(func: Callable = None, ttl: int = None, *args, **kwargs) -> "ResponseModel":
    """
    compare with run_with_result_handling,
    difference is the timeout logic.
    timeout using signal cannot work on fastapi.
    parameters:
        func is a synchronous task.
    """
    from recurvedata.executors.schemas import ResponseError, ResponseModel

    result = ResponseModel(ok=True)
    try:
        if asyncio.iscoroutinefunction(func):
            # 如果 func 是一个协程函数，直接 await 它
            data = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=ttl if ttl else None,
            )
        else:
            # 否则，使用 asyncio.to_thread 运行同步函数
            data = await asyncio.wait_for(
                asyncio.to_thread(func, *args, **kwargs),
                timeout=ttl if ttl else None,
            )
        result.data = data
    except asyncio.TimeoutError:
        raise TimeoutException(f"Function {func.__name__} timed out after {ttl} seconds")
    except Exception as e:
        result.ok = False
        if not isinstance(e, RecurveException):
            e = WrapRecurveException(ERR.UNKNOWN_ERROR, e)
        result.error = ResponseError.from_recurve_exception(e)
        traceback.print_exc()

    return result


def patch_pandas_mysql_connector_cext_missing():
    """
    Patch for MySQL Connector/Python C Extension issue.

    When pandas is imported before mysql.connector, the MySQL Connector/Python C Extension
    may be missing, which can cause connection errors like:
    '2013: Lost connection to MySQL server during query' when compiling dbt Doris models.

    This function attempts to preemptively import mysql.connector to ensure the C Extension
    is properly loaded before pandas.
    """
    try:
        # Attempt to import mysql.connector first to ensure C Extension is loaded
        import mysql.connector  # noqa: F401
    except ImportError:
        # Silently continue if mysql.connector is not installed
        # The error will be handled elsewhere if the connector is actually needed
        pass
