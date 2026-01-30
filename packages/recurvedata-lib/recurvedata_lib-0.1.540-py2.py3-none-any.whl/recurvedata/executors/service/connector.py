import concurrent.futures
import datetime
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from typing import TYPE_CHECKING

from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.connectors.dbapi import DBAPIBase
from recurvedata.connectors.service import DataSourceWrapper, get_datasource_by_config
from recurvedata.executors.schemas import ColumnItem, FullDatabaseItem, ListDatabases, Pagination, TableItem
from recurvedata.pigeon.connector.dbapi import DBAPIConnector
from recurvedata.pigeon.schema import Schema
from recurvedata.utils.normalizer import ColumnTypeNormalizer

if TYPE_CHECKING:
    from recurvedata.dbt.schemas import PreviewResult


class ConnectionService:
    @staticmethod
    def test_connection(connection_type: str, connection_config: dict):
        logging.info(f"Connection of type '{connection_type}' with provided config is valid.")
        datasource = get_datasource_by_config(connection_type, connection_config)

        def test_connection_with_timeout():
            datasource.recurve_connector.test_connection()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(test_connection_with_timeout)
            future.result()

        logging.info("Connection test successful.")

    @staticmethod
    def list_databases(connection_type: str, connection_config: dict) -> ListDatabases:
        datasource = get_datasource_by_config(connection_type, connection_config)
        logging.info(f"Listing databases for connection of type '{connection_type}' with provided config.")
        if not datasource.is_dbapi:
            logging.info(f"{datasource.ds_type} is not dbapi, not support this function")
            raise ValueError(f"{datasource.ds_type} is not dbapi, not support this function")

        return ListDatabases(items=datasource.recurve_connector.get_databases())

    @staticmethod
    def list_tables(connection_type: str, connection_config: dict, database: str) -> Pagination[TableItem]:
        datasource = get_datasource_by_config(connection_type, connection_config)
        logging.info(f"Listing tables for connection of type '{connection_type}' with provided config.")
        if not datasource.is_dbapi:
            raise ValueError(f"{datasource.ds_type} is not dbapi, not support this function")

        tables = datasource.recurve_connector.get_tables(database)
        tables = [TableItem(name=table) for table in tables]
        return Pagination[TableItem](items=tables, total=len(tables))

    @staticmethod
    def list_columns(
        connection_type: str, connection_config: dict, database_name: str, table_name: str
    ) -> Pagination[ColumnItem]:
        datasource = get_datasource_by_config(connection_type, connection_config)
        logging.info(f"Listing columns for connection of type '{connection_type}' with provided config.")
        if not datasource.is_dbapi:
            raise ValueError(f"{datasource.ds_type} is not dbapi, not support this function")

        columns = datasource.recurve_connector.get_columns(table_name, database_name)
        result = []
        for column in columns:
            normalizer = ColumnTypeNormalizer(
                connection_type, custom_mappings=datasource.recurve_connector.column_type_mapping
            )
            normalized_type = normalizer.normalize(column["type"])
            result.append(
                ColumnItem(
                    name=column["name"],
                    type=column["type"],
                    normalized_type=normalized_type,
                    comment=column.get("comment"),
                )
            )

        return Pagination[ColumnItem](items=result, total=len(result))

    @staticmethod
    def list_full_databases(connection_type: str, connection_config: dict) -> Pagination[FullDatabaseItem]:
        datasource = get_datasource_by_config(connection_type, connection_config)
        databases = datasource.recurve_connector.get_databases()

        def process_database(database: str):
            con: DBAPIBase = datasource.recurve_connector
            tables = con.get_tables(database)
            views = con.get_views(database)
            if con.connection_type == "impala":
                tables = [table for table in tables if table not in views]
            return FullDatabaseItem(
                name=database,
                tables=[TableItem(name=table) for table in tables],
                views=[TableItem(name=view) for view in views],
            )

        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_db = {executor.submit(process_database, db): db for db in databases}

            for future in as_completed(future_to_db):
                db = future_to_db[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logging.error(f"Error processing database {db}: {e}")
                    raise e

        return Pagination[FullDatabaseItem](items=results, total=len(results))

    def preview_sql(
        self,
        ds: DataSourceWrapper,
        sql: str,
        limit: int = 100,
        max_limit: int = 10000,
        orders: list[dict[str, str]] | None = None,
        offset: int = 0,
    ) -> "PreviewResult":
        from recurvedata.dbt.schemas import PreviewResult

        recurve_con = ds.recurve_connector
        limit = min(limit, max_limit)
        limited_sql = recurve_con.limit_sql(sql, limit, orders=orders, offset=offset)
        logging.info(f"preview_sql - limited_sql: {limited_sql}")
        column_schema, data = self._fetch_many_return_type(ds, limited_sql, limit)
        logging.info(f"preview_sql - fetched {len(data) if data else 0} rows")
        try:
            fields_log = []
            for field in column_schema.fields:
                field_info = {
                    "name": field.name,
                    "type": field.type,
                }
                if field.comment is not None:
                    field_info["comment"] = field.comment
                fields_log.append(field_info)
            logging.info(f"preview_sql - column_schema: {json.dumps(fields_log, default=str)}")
        except Exception as e:
            logging.info(f"preview_sql - column_schema: {column_schema} (failed to serialize: {e})")

        data = self._jsonable_value(data)
        normalizer = ColumnTypeNormalizer(recurve_con.connection_type, custom_mappings=recurve_con.column_type_mapping)
        columns = [
            ColumnItem(
                name=field.name,
                type=field.type,
                normalized_type=normalizer.normalize(field.type),
                comment=field.comment,
            )
            for field in column_schema.fields
        ]
        return PreviewResult(
            compiled_sql=sql,
            columns=columns,
            data=data,
        )

    def validate_sql(
        self,
        ds: DataSourceWrapper,
        sql: str,
        limit: int = 0,
        max_limit: int = 100,
    ) -> "SqlValidationResult":
        """
        Validate SQL by executing it and checking for syntax/runtime errors.

        This function executes ANY SQL (SELECT, DDL, DML) to validate syntax and logic.
        Use limit=0 to avoid returning large datasets for non-SELECT statements.

        Args:
            ds: DataSourceWrapper containing connection info
            sql: SQL statement(s) to validate
            limit: Maximum rows to return (0 = no data returned, just validation)
            max_limit: Maximum allowed limit

        Returns:
            SqlValidationResult with validation status and error details
        """
        import traceback

        from recurvedata.server.data_service.schemas import SqlValidationResult

        try:
            recurve_con = ds.recurve_connector
            limit = min(limit, max_limit)
            rollback_supported = True  # Default to True, will be set to False for databases that don't support it

            # For validation, we don't need to limit non-SELECT statements
            validation_sql = sql
            if limit > 0:
                # Only apply limit if we want to return data (SELECT statements)
                validation_sql = recurve_con.limit_sql(sql, limit)

            logging.info(f"validate_sql - executing: {validation_sql}")

            # Detect if this is a SELECT query or not
            sql_upper = validation_sql.strip().upper()
            is_select_query = sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")

            if is_select_query and limit > 0:
                # For SELECT queries, fetch results if limit > 0
                column_schema, data = self._fetch_many_return_type(ds, validation_sql, limit)
                logging.info(f"validate_sql - SELECT executed successfully, fetched {len(data) if data else 0} rows")

                # Prepare column information
                columns = []
                if column_schema and hasattr(column_schema, "fields"):
                    normalizer = ColumnTypeNormalizer(
                        recurve_con.connection_type, custom_mappings=recurve_con.column_type_mapping
                    )
                    columns = [
                        {
                            "name": field.name,
                            "type": field.type,
                            "normalized_type": normalizer.normalize(field.type),
                            "comment": field.comment,
                        }
                        for field in column_schema.fields
                    ]

                # Convert data to JSON-serializable format
                json_data = self._jsonable_value(data) if data else []
            else:
                # For DDL/DML queries or SELECT with limit=0, validate WITHOUT committing changes
                cursor_options = {"commit_on_close": False}  # Don't commit - we'll rollback
                connector: DBAPIConnector = ds.connector
                with connector.cursor(**cursor_options) as cursor:
                    # Initialize connection state variables outside try block
                    conn = cursor.connection
                    original_autocommit = None

                    try:
                        # Save original autocommit state and ensure it's disabled for transactions
                        if hasattr(conn, "autocommit"):
                            original_autocommit = conn.autocommit
                            if original_autocommit:
                                conn.autocommit = False

                        # Execute the SQL to validate syntax and logic
                        cursor.execute(validation_sql)

                        # Get affected rows count for logging
                        affected_rows = cursor.rowcount if hasattr(cursor, "rowcount") else 0

                        # IMPORTANT: Rollback to undo any changes - this is validation only!
                        # But only if the connection supports rollback (PostgreSQL, MySQL, etc.)
                        if hasattr(conn, "rollback"):
                            conn.rollback()
                            rollback_supported = True
                            rollback_status = "(rolled back)"
                        else:
                            # BigQuery and some other databases don't support rollback
                            # The DDL/DML will be executed and committed automatically
                            rollback_supported = False
                            rollback_status = "(auto-committed - no rollback support)"

                        # Restore original autocommit state if we changed it
                        if original_autocommit is not None and original_autocommit:
                            conn.autocommit = original_autocommit

                        logging.info(
                            f"validate_sql - DDL/DML validated successfully {rollback_status}, would affect {affected_rows} rows"
                        )

                    except Exception as e:
                        # If there's an error, rollback anyway to be safe (if supported)
                        try:
                            if hasattr(conn, "rollback"):
                                conn.rollback()
                            # Restore original autocommit state if we changed it
                            if original_autocommit is not None and original_autocommit:
                                conn.autocommit = original_autocommit
                        except:
                            pass  # Ignore rollback errors if connection is broken
                        raise e  # Re-raise the original validation error

                columns = []
                json_data = []

            # Add warning message if rollback is not supported
            warning_message = None
            if not rollback_supported and not is_select_query:
                warning_message = "WARNING: Database does not support rollback. DDL/DML changes were permanently applied to the database during validation."

            return SqlValidationResult(
                is_valid=True,
                compiled_sql=sql,
                columns=columns,
                data=json_data if limit > 0 else [],
                error_message=warning_message,
                error_code=None,
                error_traceback=None,
            )

        except Exception as e:
            # SQL validation failed - capture error details
            error_message = str(e)
            error_traceback = traceback.format_exc()

            logging.error(f"validate_sql - failed: {error_message}")
            logging.error(f"validate_sql - traceback: {error_traceback}")

            return SqlValidationResult(
                is_valid=False,
                compiled_sql=sql,
                columns=[],
                data=[],
                error_message=error_message,
                error_code=getattr(e, "code", "VALIDATION_ERROR"),
                error_traceback=error_traceback,
            )

    def _fetch_many_return_type(self, ds: DataSourceWrapper, sql: str, limit: int) -> tuple[Schema, list[tuple]]:
        cursor_options = {"commit_on_close": False}
        connector: DBAPIConnector = ds.connector
        with connector.cursor(**cursor_options) as cursor:
            cursor.execute(sql)

            # Postgres use server side cursor, need fetch first to get cursor.description
            first_row = None
            if connector.is_postgres() or connector.is_redshift():
                limit = max(0, limit - 1)
                first_row = cursor.fetchone()

            schema = self._extract_column_info_from_cursor(ds.recurve_connector, cursor)
            rv = cursor.fetchmany(limit)
            if first_row:
                rv = [first_row] + rv
            if connector.is_google_bigquery():
                # row is google.cloud.bigquery.table.Row type
                rv = [row.values() for row in rv]
            if connector.is_mssql():
                rv = [tuple(row) for row in rv]

        return schema, rv

    @staticmethod
    def _extract_column_info_from_cursor(recurve_con: RecurveConnectorBase, cursor) -> Schema:
        schema = Schema()
        for item in cursor.description:
            name = item[0]
            if "." in name:
                name = name.split(".")[1]

            type_code = item[1]
            size = item[3]
            ttype = recurve_con.sqlalchemy_column_type_code_to_name(type_code, size)
            schema.add_field_by_attrs(name, ttype, size)
        return schema

    def _jsonable_value(self, value):
        if value is None:
            return value
        elif isinstance(value, (int, float, Decimal)):
            return str(value)
        elif isinstance(value, bool):
            return value
        elif isinstance(value, dict):
            return {k: self._jsonable_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple, set)):
            return [self._jsonable_value(v) for v in value]
        elif isinstance(value, (datetime.datetime, datetime.date)):
            return value.isoformat()
        else:
            return str(value)

    @staticmethod
    def fetch_total(ds: DataSourceWrapper, sql: str) -> int:
        recurve_con: RecurveConnectorBase = ds.recurve_connector
        count_sql = recurve_con.count_sql(sql)
        connector: DBAPIConnector = ds.connector
        with connector.cursor() as cursor:
            cursor.execute(count_sql)
            return cursor.fetchone()[0]

    @staticmethod
    def create_table(
        ds: DataSourceWrapper,
        table: str,
        columns: list[ColumnItem],
        keys: list[str] = None,
        if_not_exists: bool = True,
        database: str = None,
        schema: str = None,
        **kwargs,
    ) -> bool:
        recurve_con: RecurveConnectorBase = ds.recurve_connector
        _database = database or ds.database
        sql = recurve_con.create_table_sql(
            table, columns, keys, database=_database, schema=schema, if_not_exists=if_not_exists, **kwargs
        )

        connector: DBAPIConnector = ds.connector
        with connector.cursor() as cursor:
            cursor.execute(sql)
            return True
