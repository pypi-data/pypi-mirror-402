from typer import Option

connection_type = Option(
    ..., "--connection-type", help="Type of the connection (e.g., 'mysql', 'postgresql', 'snowflake')"
)
connection_config = Option(..., "--config", help="JSON string of connection configuration")
result_filename = Option(None, "--result-filename", help="Filename to save the json result")
timeout = Option(30, "--timeout", help="Timeout for the connection test in seconds")
database = Option(..., "--database", help="Database name")
table = Option(..., "--table", help="Table name")
project_id = Option(..., "--project-id", help="Project ID")
connection_name = Option(..., "--connection-name", help="Connection Name")
alias = Option(..., "--alias", help="Alias")  # project connection name
limit = Option(100, "--limit")
sql = Option(..., "--sql")
tracing_context = Option(None, "--tracing-context", help="Tracing context")
force_regenerate_dir = Option(False, "--force-regenerate-dir", help="Whether to force regenerate dbt project")
no_data = Option(False, "--no-data", help="Whether to include data in preview result")
