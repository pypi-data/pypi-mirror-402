import typer

from recurvedata.consts import ScheduleType
from recurvedata.executors.cli.connector import cli as connector_cli
from recurvedata.executors.cli.dbt import cli as dbt_cli
from recurvedata.executors.debug_executor import DebugExecutor
from recurvedata.executors.executor import Executor
from recurvedata.utils import init_logging
from recurvedata.utils._typer import RecurveTyper
from recurvedata.utils.date_time import astimezone

cli = RecurveTyper()
cli.add_typer(connector_cli, name="connector")
cli.add_typer(dbt_cli, name="dbt")


@cli.callback()
def init():
    from recurvedata.core.tracing import Tracing

    if not Tracing.is_instantiated():
        from recurvedata.utils.tracing import create_dp_tracer

        create_dp_tracer("recurve-lib")
    init_logging()


@cli.command()
def execute(
    dag_slug: str = typer.Option(..., "--dag_slug", help="Unique identifier for the DAG"),
    node_slug: str = typer.Option(..., "--node_slug", help="Unique identifier for the node"),
    execution_date: str = typer.Option(..., "--execution_date", help="Date/time of execution"),
    # RecurveLink settings
    link_workflow_id: int = typer.Option(None, "--link_workflow_id", help="ID of linked workflow"),
    link_node_id: int = typer.Option(None, "--link_node_id", help="ID of linked node"),
    is_link_workflow: bool = typer.Option(False, "--is_link_workflow", help="Whether this is a linked workflow"),
):
    """
    Execute a specific node in a DAG at the given execution date.

    Optionally configure workflow linking settings.
    """
    # Initialize and run the executor
    executor = Executor(dag_slug=dag_slug, node_slug=node_slug, execution_date=execution_date)
    executor.set_link_settings(
        link_workflow_id=link_workflow_id, link_node_id=link_node_id, is_link_workflow=is_link_workflow
    )
    executor.run()


@cli.command()
def debug(
    workflow_id: int = typer.Option(..., "--workflow_id", help="ID of the workflow to debug"),
    node_key: str = typer.Option(..., "--node_key", help="Key identifier of the node to debug"),
    schedule_type: ScheduleType = typer.Option(..., "--schedule_type", help="Type of schedule"),
    schedule_interval: str = typer.Option(..., "--schedule_interval", help="Schedule interval specification"),
    execution_date: str = typer.Option(..., "--execution_date", help="Execution timestamp"),
    timezone: str = typer.Option(..., "--timezone", help="Timezone for execution"),
    celery_task_id: str = typer.Option(..., "--celery_task_id", help="Celery task ID for tracking"),
):
    """
    Debug a workflow node by executing it in isolation.

    This command allows debugging a specific node from a workflow by running it independently.
    The execution context (schedule, timing, etc) can be controlled via the parameters.
    """
    # execution_date = ensure_datetime(execution_date).replace(tzinfo=ensure_tz(timezone))
    execution_date = astimezone(execution_date, timezone)
    executor = DebugExecutor(
        workflow_id=workflow_id,
        node_key=node_key,
        schedule_type=schedule_type,
        schedule_interval=schedule_interval,
        execution_date=execution_date,
        timezone=timezone,
        celery_task_id=celery_task_id,
    )
    executor.run()


if __name__ == "__main__":
    cli()
