import json

import typer

from recurvedata.executors.service.connector import ConnectionService
from recurvedata.executors.utils import run_with_result_handling
from recurvedata.utils import init_logging
from recurvedata.utils._typer import RecurveTyper

cli = RecurveTyper()


@cli.callback()
def init():
    init_logging()


@cli.command()
def test_connection(
    connection_type: str = typer.Option(
        ..., "--connection-type", help="Type of the connection (e.g., 'mysql', 'postgresql', 'snowflake')"
    ),
    config: str = typer.Option(..., "--config", help="JSON string of connection configuration"),
    result_filename: str = typer.Option(None, "--result-filename", help="Filename to save the json result"),
    timeout: int = typer.Option(30, "--timeout", help="Timeout for the connection test in seconds"),
):
    """
    Test if a connection is valid
    """
    connection_config = json.loads(config)
    run_with_result_handling(
        ConnectionService.test_connection, timeout, result_filename, connection_type, connection_config
    )


@cli.command()
async def list_databases(
    connection_type: str = typer.Option(
        ..., "--connection-type", help="Type of the connection (e.g., 'mysql', 'postgresql', 'snowflake')"
    ),
    config: str = typer.Option(..., "--config", help="JSON string of connection configuration"),
    result_filename: str = typer.Option(None, "--result-filename", help="Filename to save the json result"),
):
    """
    List databases for a given connection
    """
    connection_config = json.loads(config)
    run_with_result_handling(
        ConnectionService.list_databases,
        result_filename=result_filename,
        connection_type=connection_type,
        connection_config=connection_config,
    )


@cli.command()
async def list_tables(
    connection_type: str = typer.Option(
        ..., "--connection-type", help="Type of the connection (e.g., 'mysql', 'postgresql', 'snowflake')"
    ),
    config: str = typer.Option(..., "--config", help="JSON string of connection configuration"),
    database: str = typer.Option(..., "--database", help="Database name"),
    result_filename: str = typer.Option(None, "--result-filename", help="Filename to save the json result"),
):
    """List tables for a given connection and database"""
    connection_config = json.loads(config)
    run_with_result_handling(
        ConnectionService.list_tables,
        result_filename=result_filename,
        connection_type=connection_type,
        connection_config=connection_config,
        database=database,
    )


@cli.command()
async def list_columns(
    connection_type: str = typer.Option(
        ..., "--connection-type", help="Type of the connection (e.g., 'mysql', 'postgresql', 'snowflake')"
    ),
    config: str = typer.Option(..., "--config", help="JSON string of connection configuration"),
    database: str = typer.Option(..., "--database", help="Database name"),
    table: str = typer.Option(..., "--table", help="Table name"),
    result_filename: str = typer.Option(None, "--result-filename", help="Filename to save the json result"),
):
    """List columns for a given connection, database and table"""
    connection_config = json.loads(config)
    run_with_result_handling(
        ConnectionService.list_columns,
        result_filename=result_filename,
        connection_type=connection_type,
        connection_config=connection_config,
        database_name=database,
        table_name=table,
    )


@cli.command()
async def list_full_databases(
    connection_type: str = typer.Option(
        ..., "--connection-type", help="Type of the connection (e.g., 'mysql', 'postgresql', 'snowflake')"
    ),
    config: str = typer.Option(..., "--config", help="JSON string of connection configuration"),
    result_filename: str = typer.Option(None, "--result-filename", help="Filename to save the json result"),
):
    """List full databases for a given connection"""
    connection_config = json.loads(config)
    run_with_result_handling(
        ConnectionService.list_full_databases,
        result_filename=result_filename,
        connection_type=connection_type,
        connection_config=connection_config,
    )


if __name__ == "__main__":
    cli()
