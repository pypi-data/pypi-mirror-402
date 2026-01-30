import hashlib
import json
import os
import traceback
from typing import Any

from sqlalchemy.engine.url import URL

from recurvedata.connectors._register import get_connection_class
from recurvedata.connectors.config_schema import ALL_CONFIG_SCHEMA_DCT, get_complex_config_schema
from recurvedata.connectors.const import (  # noqa
    ALL_CONNECTION_SECRET_WORDS,
    DBAPI_TYPES,
    JUICE_SYNC_ABLE_DBAPI_TYPES,
    SQL_OPERATOR_TYPES,
)
from recurvedata.connectors.datasource import DataSource, DataSourceWrapper
from recurvedata.connectors.pigeon import DataSource as PigeonDataSource
from recurvedata.consts import PROJECT_ID_KEY


def list_config_schemas(only_enabled=True) -> list[dict[str, Any]]:
    """
    todo: 返回的类型 (看要不要用 pydantic)
    :param only_enabled:
    :return:
    """
    config_schemas = ALL_CONFIG_SCHEMA_DCT.values()
    if only_enabled:
        config_schemas = filter(lambda v: v["enabled"], config_schemas)
    return list(config_schemas)


def get_config_schema(connection_type: str):
    complex_config_schema = get_complex_config_schema(connection_type)
    if complex_config_schema:
        return complex_config_schema["config_schema"]


def get_connection_category(connection_type: str):
    complex_config_schema = get_complex_config_schema(connection_type)
    if complex_config_schema:
        return complex_config_schema["category"]


def get_connection_ui_category(connection_type: str):
    complex_config_schema = get_complex_config_schema(connection_type)
    if complex_config_schema:
        return complex_config_schema["ui_category"]


def get_connection_type(connection_type: str):
    complex_config_schema = get_complex_config_schema(connection_type)
    if complex_config_schema:
        return complex_config_schema["type"]


def get_connection_ui_type(connection_type: str):
    complex_config_schema = get_complex_config_schema(connection_type)
    if complex_config_schema:
        return complex_config_schema["ui_type"]


def get_connection_host(ui_type: str, connection_conf: dict):
    """
    前端页面列表页显示的 ui_type
    :param ui_type:
    :param connection_conf:
    :return:
    """
    for keyword in ["host", "endpoint", "access_key_id", "url"]:  # todo: not so good
        if keyword in connection_conf:
            return connection_conf[keyword]
    return ""


def get_all_secret_keywords():
    return ALL_CONNECTION_SECRET_WORDS


def test_connection(connection_type: str, connection_conf: dict) -> tuple[bool, str]:
    connection_cls = get_connection_class(connection_type)
    try:
        con = connection_cls(connection_conf)
        con.test_connection()
        return True, ""
    except Exception:
        return False, traceback.format_exc()


def init_connector(connection_type: str, connection_conf: dict):
    pass


def list_dbapi_types():
    return DBAPI_TYPES


def list_juice_sync_able_dbapi_types():
    return JUICE_SYNC_ABLE_DBAPI_TYPES


def list_sql_operator_types():
    return SQL_OPERATOR_TYPES


def get_datasource_by_name(project_connection_name: str, project_id: int | None = None) -> DataSourceWrapper:
    from recurvedata.executors.client import ExecutorClient
    from recurvedata.executors.schemas import ConnectionItem

    project_id = os.environ.get(PROJECT_ID_KEY) if project_id is None else project_id
    if project_id is None:
        raise ValueError("project id is not set")

    recurve_client = ExecutorClient()
    conn: ConnectionItem = recurve_client.get_connection(project_id=project_id, connection_name=project_connection_name)
    if PigeonDataSource.is_support_connection_type(conn.type):
        try:
            return DataSourceWrapper(PigeonDataSource(connection_type=conn.type, name=conn.name, data=conn.data))
        except ModuleNotFoundError:
            pass
    return DataSourceWrapper(DataSource(connection_type=conn.type, name=conn.name, data=conn.data))


def get_datasource_by_config(
    connection_type: str, config: dict, name: str = None, database: str = None, schema: str = None
) -> DataSourceWrapper:
    """
    Get a DataSourceWrapper instance based on the connection type and configuration dictionary.

    :param connection_type: The type of the connection (e.g., 'mysql', 'postgresql', 'snowflake')
    :param config: A dictionary containing the connection configuration
    :param database: project database name
    :param schema: project schema name if have
    :return: A DataSourceWrapper instance
    """
    update_dct = {}
    if database:
        update_dct.update({"database": database})
    if schema:
        update_dct.update({"schema": schema})
    config.update(update_dct)
    if PigeonDataSource.is_support_connection_type(connection_type):
        try:
            return DataSourceWrapper(PigeonDataSource(connection_type=connection_type, name=name, data=config))
        except ModuleNotFoundError:
            pass
    return DataSourceWrapper(DataSource(connection_type=connection_type, name=name, data=config))


def get_sqlalchemy_url_by_connection(connection_orm) -> URL:
    ds = DataSourceWrapper(
        DataSource(connection_type=connection_orm.type, name=connection_orm.name, data=connection_orm.data)
    )
    if not ds.is_dbapi:
        raise ValueError(f"{ds.ds_type} is not dbapi, not support this function")
    con = ds.recurve_connector
    return con.sqlalchemy_url


# todo: cache
def list_column_data_types():
    import sqlalchemy.sql.sqltypes

    def _get_module_types(module):
        types = set()
        for cls_name, cls in module.__dict__.items():
            if cls_name.startswith("_"):
                continue
            if not isinstance(cls, type):
                continue
            if not issubclass(cls, sqlalchemy.sql.sqltypes.TypeEngine):
                continue
            if not hasattr(cls, "__visit_name__"):
                continue
            if cls.__visit_name__ in ("TypeDecorator", "type_decorator"):
                continue
            types.add(cls.__visit_name__.lower())
        return types

    types = _get_module_types(sqlalchemy.sql.sqltypes)
    try:
        import sqlalchemy.dialects.mysql.types

        types = types.union(_get_module_types(sqlalchemy.dialects.mysql.types))
    except ImportError:
        pass

    try:
        import clickhouse_sqlalchemy.types.common

        types = types.union(_get_module_types(clickhouse_sqlalchemy.types))
    except ImportError:
        pass

    return sorted(types)


def convert_connection_to_dbt_profile(
    connection_type: str, connection_config: dict, database: str, schema: str = None
) -> dict:
    ds = get_datasource_by_config(connection_type, connection_config, database=database, schema=schema)
    if not ds.is_dbapi:
        return {}
    con = ds.recurve_connector

    dct = con.convert_config_to_dbt_profile(database, schema)
    return dct


def convert_connection_to_cube_config(
    connection_type: str, connection_config: dict, database: str, schema: str = None, masking: bool = None
) -> dict:
    ds = get_datasource_by_config(connection_type, connection_config, database=database, schema=schema)
    con = ds.recurve_connector
    dct = con.convert_config_to_cube_config(database, schema, ds)
    if not dct or not isinstance(dct, dict):
        return {}

    masking = masking if masking is not None else not ds.is_dbapi
    if masking:
        return {k: hashlib.md5(json.dumps(dct[k]).encode("utf-8")).hexdigest() for k in dct}
    return dct
