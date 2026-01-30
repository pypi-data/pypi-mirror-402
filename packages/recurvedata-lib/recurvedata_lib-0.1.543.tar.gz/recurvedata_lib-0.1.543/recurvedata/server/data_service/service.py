import os
import tempfile
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Literal

import pandas as pd
from loguru import logger

from recurvedata.config import SERVER_RESULT_STAGING_PATH
from recurvedata.connectors.service import get_datasource_by_config
from recurvedata.core.templating import Renderer
from recurvedata.dbt.schemas import PreviewResult
from recurvedata.exceptions import ERR, WrapRecurveException, wrap_error
from recurvedata.executors.cli.connector import ConnectionService
from recurvedata.executors.executor import Executor
from recurvedata.executors.schemas import Pagination
from recurvedata.filestorage import StorageType
from recurvedata.filestorage import factory as filestorage_factory
from recurvedata.pigeon.dumper import new_to_csv_dumper
from recurvedata.server.data_service.client import DataServiceClient
from recurvedata.server.data_service.consts import FIELD_TYPE_MAP
from recurvedata.server.data_service.schemas import DownloadResult, SqlValidationResult
from recurvedata.utils.date_time import now
from recurvedata.utils.sql import extract_order_by_from_sql


@dataclass
class DataServiceService:
    project_id: int
    project_connection_id: int
    variables: dict = None

    @cached_property
    def client(self):
        return DataServiceClient()

    def prepare_variables(self, variables: dict | None) -> dict:
        logger.info("start process variables")
        execution_date, schedule_interval = now(), "@daily"
        processed_variables = Executor.process_variables(variables or {}, {}, execution_date, schedule_interval)
        result_variables = Renderer().init_context(execution_date, schedule_interval)
        result_variables.update(processed_variables)
        return result_variables

    @wrap_error(ERR.DP_FETCH_CONNECTION_FAILED)
    def fetch_connection_and_variables(self):
        logger.info("start fetch connection and variables")
        item = self.client.get_connection_and_variables(self.project_id, self.project_connection_id)
        con_item = item.connection
        logger.info("after fetch connection and variables")
        self.ds = get_datasource_by_config(
            con_item.type, config=con_item.data, database=con_item.database, schema=con_item.database_schema
        )
        self.variables = self.prepare_variables(item.variables)

    def preview(
        self, sql: str, limit: int, no_data: bool = False, orders: list[dict[str, str]] | None = None, offset: int = 0
    ) -> PreviewResult:
        self.fetch_connection_and_variables()
        rendered_sql = Renderer().render_template(sql, self.variables)
        if no_data:
            limit = 0

        con_service = ConnectionService()
        try:
            result = con_service.preview_sql(self.ds, rendered_sql, limit, orders=orders, offset=offset)
            columns = result.columns
            column_names = set()
            for col in columns:
                if col.name in column_names:
                    raise ValueError(f"duplicate column name: {col.name}, please check your sql query")
                column_names.add(col.name)

            return result

        except Exception as e:
            logger.error(f"Failed to preview data: {e}")
            raise WrapRecurveException(ERR.PREVIEW_DATA_FAILED, e)

    async def download(
        self,
        *,
        storage_type: StorageType,
        storage_options: dict[str, Any],
        file_name: str,
        sql: str,
        tenant_id: int,
        project_id: int,
        user_id: int,
        orders: list[dict[str, str]] | None = None,
        file_type: Literal["csv", "xlsx"] = "csv",
        fields: list[dict] | None = None,
    ) -> PreviewResult:
        self.fetch_connection_and_variables()
        rendered_sql = Renderer().render_template(sql, self.variables)

        connection = self.ds.data.copy()
        connection.pop("database", None)
        recurve_con = self.ds.recurve_connector
        ordered_sql = recurve_con.order_sql(rendered_sql, orders=orders)

        result_file_name = tempfile.mktemp(dir=SERVER_RESULT_STAGING_PATH)
        os.makedirs(os.path.dirname(result_file_name), exist_ok=True)
        open(result_file_name, "w").close()
        logger.info(f"result_file_name: {result_file_name}")

        logger.info("start dump data")
        dumper = new_to_csv_dumper(
            dbtype=self.ds.ds_type,
            connection=connection,
            database=self.ds.database,
            connector=self.ds.connector,
            sql=ordered_sql,
            filename=result_file_name,
            write_header=True,
            merge_files=True,
        )

        dumper.execute()

        logger.info(f"result_file_name size: {os.path.getsize(result_file_name)}")

        if os.path.getsize(result_file_name) == 0:
            return DownloadResult(file_name="")

        dtype = {}
        rename_dict = None

        if fields:
            for field in fields:
                field_type = FIELD_TYPE_MAP.get(field.get("field_type"))
                if field_type:
                    dtype[field["name"]] = field_type

            _rename_dict = {field["name"]: field["alias"] or field["name"] for field in fields}
            if any([k != v for k, v in _rename_dict.items()]):
                rename_dict = _rename_dict

        if file_type == "xlsx" or rename_dict:
            df = pd.read_csv(result_file_name, dtype=dtype)

            if rename_dict:
                df.rename(columns=lambda x: rename_dict.get(x, x), inplace=True)

            if file_type == "xlsx":
                if not result_file_name.endswith(".xlsx"):
                    result_file_name += ".xlsx"
                df.to_excel(result_file_name, index=False)
            else:
                df.to_csv(result_file_name, index=False)

        if not file_name.endswith(file_type):
            file_name += f".{file_type}"

        file_name = f"{tenant_id}/{project_id}/{user_id}/{file_name}"

        logger.info("start upload file")
        storage = filestorage_factory.create(storage_type, storage_options)
        with open(result_file_name, "rb") as f:
            file_content = f.read()
            await storage.write_bytes(file_name, file_content)
        logger.info("upload file success")

        return DownloadResult(file_name=file_name)

    def preview_total(
        self,
        sql: str,
        limit: int,
        no_data: bool = False,
        orders: list[dict[str, str]] | None = None,
        offset: int = 0,
    ) -> Pagination[dict[str, Any]]:
        preview_result = self.preview(sql, limit, no_data, orders, offset)

        items = []
        for row in preview_result.data:
            row_data = {}
            for col, value in zip(preview_result.columns, row):
                row_data[col.name] = {
                    "type": col.type,
                    "name": col.name,
                    "normalized_type": col.normalized_type,
                    "value": value,
                }
            items.append(row_data)

        con_service = ConnectionService()
        total = con_service.fetch_total(self.ds, sql)

        return Pagination[dict[str, Any]](
            items=items,
            total=total,
        )

    def fetch_count(self, sql: str) -> int:
        self.fetch_connection_and_variables()
        rendered_sql = Renderer().render_template(sql, self.variables)
        con_service = ConnectionService()
        return con_service.fetch_total(self.ds, rendered_sql)

    def validate_sql(self, sql: str, limit: int = 0) -> SqlValidationResult:
        """
        Validate SQL by executing it and checking for syntax/runtime errors.
        Supports any SQL statement type including DDL, DML, and SELECT.

        Args:
            sql: SQL statement(s) to validate
            limit: Maximum rows to return (0 = no data returned, just validation)

        Returns:
            SqlValidationResult with validation status and error details
        """

        self.fetch_connection_and_variables()
        rendered_sql = Renderer().render_template(sql, self.variables)
        con_service = ConnectionService()
        return con_service.validate_sql(self.ds, rendered_sql, limit=limit)

    def direct_query(
        self, connection_type: str, connection_data: dict, sql: str, limit: int = 100, offset: int = 0
    ) -> PreviewResult:
        """
        Execute SQL directly on a connection without any limitations or modifications.

        Args:
            connection_type: The type of connection (e.g. mysql, hive, s3)
            connection_data: Connection configuration details
            sql: SQL statement to execute
            limit: Maximum number of rows to return (default: 100)
            offset: Number of rows to skip before starting to return rows

        Returns:
            PreviewResult with raw data and column information
        """
        # Create datasource from connection config
        self.ds = get_datasource_by_config(
            connection_type, config=connection_data, database=connection_data.get("database")
        )

        # Extract ORDER BY from SQL if present
        recurve_con = self.ds.recurve_connector
        dialect = recurve_con.get_dialect() if hasattr(recurve_con, "get_dialect") else connection_type
        orders = extract_order_by_from_sql(sql, dialect)

        # Use existing preview_sql with custom limit and offset
        # Pass extracted orders to ensure ORDER BY is applied at outer level
        con_service = ConnectionService()
        try:
            result = con_service.preview_sql(self.ds, sql, limit=limit, max_limit=limit, orders=orders, offset=offset)
            return result
        except Exception as e:
            logger.error(f"Failed to execute direct query: {e}")
            raise WrapRecurveException(ERR.PREVIEW_DATA_FAILED, e)
