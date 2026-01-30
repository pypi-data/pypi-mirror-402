import logging

from recurvedata.client.server_client import ServerDbtClient
from recurvedata.core.tracing import Tracing
from recurvedata.executors.cli import parameters as param
from recurvedata.executors.utils import run_with_result_handling
from recurvedata.utils import init_logging
from recurvedata.utils._typer import RecurveTyper
from recurvedata.utils.sql import trim_replace_special_character

dbt_tracer = Tracing()
cli = RecurveTyper()
logger = logging.getLogger(__name__)


@cli.callback()
def init():
    from recurvedata.core.tracing import Tracing

    if not Tracing.is_instantiated():
        from recurvedata.utils.tracing import create_dp_tracer

        create_dp_tracer("recurve-lib-dbt")
    init_logging()


@cli.command()
@dbt_tracer.create_span(context_payload_name="tracing_context")
async def compile(
    project_id: int = param.project_id,
    alias: str = param.alias,
    sql: str = param.sql,
    tracing_context: str = param.tracing_context,
    force_regenerate_dir: bool = param.force_regenerate_dir,
    result_filename: str = param.result_filename,
):
    try:
        _compile_using_server(project_id, alias, sql, force_regenerate_dir, result_filename)
    except Exception as e:
        logger.exception(f"_compile_using_server failed: {e}, try _compile_using_service")
        _compile_using_service(project_id, alias, sql, force_regenerate_dir, result_filename)


@dbt_tracer.create_span()
def _compile_using_server(project_id: int, alias: str, sql: str, force_regenerate_dir: bool, result_filename: str):
    client = ServerDbtClient()
    res = client.compile(project_id, sql, alias, force_regenerate_dir)
    if result_filename:
        res.model_dump_json_file(result_filename)


@dbt_tracer.create_span()
def _compile_using_service(
    project_id: int, alias: str, sql: str, force_regenerate_dir: bool, result_filename: str = param.result_filename
):
    from recurvedata.dbt.service import DbtService

    sql = trim_replace_special_character(sql)
    service = DbtService(
        project_id=project_id,
        project_connection_name=alias,
        force_regenerate_dir=force_regenerate_dir,
        need_fetch_variable=True,
    )
    run_with_result_handling(service.compile, inline_sql=sql, result_filename=result_filename)


@cli.command()
async def preview(
    project_id: int = param.project_id,
    alias: str = param.alias,
    sql: str = param.sql,
    limit: int = param.limit,
    no_data: bool = param.no_data,
    force_regenerate_dir: bool = param.force_regenerate_dir,
    result_filename: str = param.result_filename,
):
    try:
        _preview_using_server(project_id, alias, sql, limit, force_regenerate_dir, result_filename)  # todo: add no_data
    except Exception as e:
        logger.exception(f"_preview_using_server failed: {e}, try _preview_using_service")
        _preview_using_service(project_id, alias, sql, limit, force_regenerate_dir, no_data, result_filename)


def _preview_using_server(
    project_id: int, alias: str, sql: str, limit: int, force_regenerate_dir: bool, result_filename: str
):
    client = ServerDbtClient()
    res = client.preview(project_id, sql, alias, limit, force_regenerate_dir)
    if result_filename:
        res.model_dump_json_file(result_filename)


def _preview_using_service(
    project_id: int,
    alias: str,
    sql: str,
    limit: int,
    force_regenerate_dir: bool,
    no_data: bool,
    result_filename: str = param.result_filename,
):
    from recurvedata.dbt.service import DbtService

    sql = trim_replace_special_character(sql, strip_sufix=True)
    service = DbtService(
        project_id=project_id,
        project_connection_name=alias,
        force_regenerate_dir=force_regenerate_dir,
        need_fetch_variable=True,
    )
    run_with_result_handling(
        service.preview, inline_sql=sql, limit=limit, result_filename=result_filename, no_data=no_data
    )


if __name__ == "__main__":
    cli()
