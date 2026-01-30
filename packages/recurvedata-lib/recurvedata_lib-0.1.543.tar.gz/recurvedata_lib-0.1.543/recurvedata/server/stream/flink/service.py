"""Service layer for Flink Stream API operations"""

import logging
from datetime import datetime

from recurvedata.connectors.service import get_datasource_by_config
from recurvedata.exceptions import RecurveException
from recurvedata.executors.client import ExecutorClient
from recurvedata.executors.models import DataSource
from recurvedata.executors.schemas import ColumnItem, ConnectionItem
from recurvedata.executors.service.connector import ConnectionService
from recurvedata.operators.stream_operator.const import (
    SINK_TYPE_DORIS,
    SINK_TYPE_STARROCKS,
    SOURCE_TYPE_POSTGRES,
    STREAM_SINK_TYPES,
    STREAM_SOURCE_TYPES,
    SUPPORTED_COMBINATIONS,
)
from recurvedata.server.stream.flink.const import ERROR_JOB_NOT_FOUND, SUCCESS_JOB_CREATED
from recurvedata.server.stream.flink.error_codes import ERR
from recurvedata.server.stream.flink.rest_client import FlinkRestClient
from recurvedata.server.stream.flink.schema import (
    CancelJobPayload,
    CreateJobData,
    CreateJobPayload,
    FlinkConfig,
    FlinkJobStatus,
    JobDetails,
    JobSummary,
    SinkConfig,
    SourceConfig,
    TransformConfig,
)
from recurvedata.server.stream.flink.sql_gateway_client import FlinkSQLGatewayClient
from recurvedata.server.stream.flink.utils import (
    build_cdc_config_by_datasource,
    build_sink_config_by_datasource,
    convert_column_type_to_flink_type,
)

logger = logging.getLogger(__name__)


class FlinkService:
    @staticmethod
    def _get_connection_by_name(
        project_id: int, connection_name: str, client: ExecutorClient | None = None
    ) -> ConnectionItem:
        if client is None:
            client = ExecutorClient()
        connection = client.get_connection(project_id=project_id, connection_name=connection_name)
        if not connection:
            raise RecurveException(data=f"Connection not found: {connection_name}")
        return connection

    @staticmethod
    def _convert_connection_to_datasource(connection: ConnectionItem) -> DataSource:
        return DataSource(connection_type=connection.type, name=connection.name, data=connection.data)

    @staticmethod
    def _get_datasource_by_connection_name(
        project_id: int, connection_name: str, client: ExecutorClient | None = None
    ) -> DataSource:
        connection = FlinkService._get_connection_by_name(project_id, connection_name, client)
        datasource = FlinkService._convert_connection_to_datasource(connection)
        return datasource

    @staticmethod
    def validate_source_type(source_type: str) -> None:
        """Validate that source-sink combination is supported"""
        if source_type not in STREAM_SOURCE_TYPES:
            raise RecurveException(data=f"Unsupported source type: {source_type}")

    @staticmethod
    def validate_sink_type(sink_type: str) -> None:
        """Validate that sink type is supported"""
        if sink_type not in STREAM_SINK_TYPES:
            raise RecurveException(data=f"Unsupported sink type: {sink_type}")

    @staticmethod
    def validate_source_sink_combination(source_type: str, sink_type: str) -> None:
        """Validate that source-sink combination is supported"""
        FlinkService.validate_source_type(source_type)
        FlinkService.validate_sink_type(sink_type)
        if sink_type not in SUPPORTED_COMBINATIONS.get(source_type, []):
            raise RecurveException(data=f"Unsupported source-sink combination: {source_type} -> {sink_type}")

    @staticmethod
    def _get_flink_sql_gateway_client(
        project_id: int, flink_config: FlinkConfig, executor_client: ExecutorClient | None = None
    ) -> FlinkSQLGatewayClient:
        flink_connection = FlinkService._get_connection_by_name(
            project_id, flink_config.flink_connection_name, executor_client
        )
        return FlinkSQLGatewayClient.from_connection(flink_connection, flink_config)

    @staticmethod
    def _get_flink_rest_client(
        project_id: int, flink_connection_name: str, executor_client: ExecutorClient | None = None
    ) -> FlinkRestClient:
        flink_connection = FlinkService._get_connection_by_name(project_id, flink_connection_name, executor_client)
        return FlinkRestClient.from_connection(flink_connection)

    @staticmethod
    async def _generate_source_ddl(
        source_conn: ConnectionItem, source_conf: SourceConfig, table_name: str, flink_cdc_config: dict
    ) -> str:
        """
        Generate Flink SQL DDL for source
        Args:
            source_conn: Source connection
            source_conf: Source configuration
            table_name: Table name
            flink_cdc_config: Flink CDC configuration
        Returns:
            Flink SQL DDL for source
        """
        # Validate that source table exists before fetching columns
        FlinkService._validate_source_table_exists(source_conn, source_conf)

        # table definition
        source_columns = await FlinkService._fetch_source_columns(source_conn, source_conf)
        columns = [
            f"{column.name} {convert_column_type_to_flink_type(column.normalized_type)}" for column in source_columns
        ]
        # properties
        props = []
        for k, v in flink_cdc_config.items():
            if k is not None:
                props.append(f"'{k}' = '{v}'")

        source_ddl = f"""CREATE TABLE {table_name} (
            {", ".join(columns)}
        ) WITH (
            {", ".join(props)}
        )"""
        return source_ddl

    @staticmethod
    def _generate_sink_dml(
        source_conf: SourceConfig,
        source_conn: ConnectionItem,
        sink_conf: SinkConfig,
        sink_conn: ConnectionItem,
        flink_sink_table_name: str,
        flink_sink_config: dict,
        unique_keys: list[str],
        datasource_transform_ddl: str,
    ) -> str:
        """
        Generate Flink SQL DDL for sink
        Args:
            source_conn: Source connection
            source_conf: Source configuration
            sink_conf: Sink configuration
            datasource_transform_ddl: Data source transform DDL
            flink_sink_table_name: Flink sink table name
            flink_sink_config: Flink sink configuration
            unique_keys: Unique keys
        Returns:
            Flink SQL DDL for sink
        """
        source_ds = get_datasource_by_config(
            source_conn.type,
            config=source_conn.data,
            database=source_conf.database_name,
            schema=source_conf.schema_name,
        )

        preview_result = ConnectionService().preview_sql(ds=source_ds, sql=datasource_transform_ddl, limit=0)
        sink_columns = preview_result.columns
        dest_table_name = sink_conf.table_name
        if not sink_columns:
            raise RecurveException(data=f"No columns found for sink table {dest_table_name}")

        # Extra arguments for create table
        kwargs = {}
        if sink_conf.sink_type in (SINK_TYPE_DORIS, SINK_TYPE_STARROCKS):
            kwargs["properties"] = {
                "replication_num": 1,  # allow configuration of replication_num
            }
        # Create sink table if not exists
        sink_ds = get_datasource_by_config(
            sink_conn.type, config=sink_conn.data, database=sink_conf.database_name, schema=sink_conf.schema_name
        )
        res = ConnectionService.create_table(
            sink_ds,
            sink_conf.table_name,
            sink_columns,
            unique_keys,
            if_not_exists=True,
            database=sink_conf.database_name,
            schema=sink_conf.schema_name,
            **kwargs,
        )
        logger.info(f"create_table - result: {res}")

        flink_column_names = {column.name for column in sink_columns}
        missing_keys = [k for k in unique_keys if k not in flink_column_names]
        if missing_keys:
            raise RecurveException(data=f"Primary key {missing_keys} is not found for table: {dest_table_name}")

        flink_columns_ddl = [
            f"{column.name} {convert_column_type_to_flink_type(column.normalized_type)}" for column in sink_columns
        ]

        flink_columns_ddl.append(f"PRIMARY KEY ({', '.join(unique_keys)}) NOT ENFORCED")

        # Generate sink DDL
        props = []
        for k, v in flink_sink_config.items():
            if k is not None:
                props.append(f"'{k}' = '{v}'")
        sink_ddl = f"""CREATE TABLE {flink_sink_table_name} (
            {", ".join(flink_columns_ddl)}
        ) WITH (
            {", ".join(props)}
        )"""
        return sink_ddl

    @staticmethod
    def _generate_insert_dml_and_transform_ddl(
        source_conf: SourceConfig,
        flink_sink_table_name: str,
        flink_source_table_name: str,
        transform_sql: str | None = None,
    ) -> tuple[str, str]:
        """
        Generate Flink SQL DDL for insert
        Args:
            source_conf: Source configuration
            flink_sink_table_name: Flink sink table name
            flink_source_table_name: Flink source table name
            transform_sql: Transform SQL
        Returns:
            Flink SQL DDL for insert
        """
        transform_ddl = ""
        if transform_sql:
            transform_ddl = transform_sql.strip().strip(";").replace("source_table_name", flink_source_table_name)
        else:
            transform_ddl = f"SELECT * FROM {flink_source_table_name}"

        source_table_name = source_conf.table_name
        if source_conf.schema_name:
            source_table_name = f"{source_conf.schema_name}.{source_table_name}"
        datasource_transform_ddl = transform_ddl.replace(flink_source_table_name, source_table_name)
        insert_dml = f"INSERT INTO {flink_sink_table_name} ({transform_ddl})"
        return insert_dml, datasource_transform_ddl

    @staticmethod
    async def _generate_flink_sql_ddl_dml(
        job_name: str,
        source_conn: ConnectionItem,
        source_conf: SourceConfig,
        sink_conn: ConnectionItem,
        sink_conf: SinkConfig,
        flink_cdc_config: dict,
        flink_sink_config: dict,
        transform_config: TransformConfig,
    ) -> tuple[str, str, str, str]:
        """
        Generate Flink SQL DDL for CDC job
        Args:
            job_name: Name of the job
            source_config: Source configuration
            sink_config: Sink configuration
        Returns:
            Flink SQL DDL for CDC job

        """
        # Set job name
        set_job_name = f"SET 'pipeline.name' = '{job_name}'"

        # Generate CREATE TABLE statements for source
        source_table_name = source_conf.table_name
        flink_source_table_name = "source"
        if source_conf.schema_name:
            flink_source_table_name += f"_{source_conf.schema_name}"
        flink_source_table_name += f"_{source_table_name}".replace(".", "_")

        source_ddl = await FlinkService._generate_source_ddl(
            source_conn, source_conf, flink_source_table_name, flink_cdc_config
        )

        # Generate sink table name
        flink_sink_table_name = f"sink_{sink_conf.table_name}".replace(".", "_")

        # Generate INSERT statement
        insert_dml, datasource_transform_ddl = FlinkService._generate_insert_dml_and_transform_ddl(
            source_conf=source_conf,
            flink_sink_table_name=flink_sink_table_name,
            flink_source_table_name=flink_source_table_name,
            transform_sql=transform_config.sql,
        )

        logger.info(f"datasource_transform_ddl: {datasource_transform_ddl}")
        # Generate CREATE TABLE statements for sink
        if not transform_config.unique_key:
            raise RecurveException(data=f"Unique key is not found for table: {sink_conf.table_name}")
        unique_keys = [k.strip() for k in transform_config.unique_key.split(",")]
        logger.warning(f"1. sink_conf: {sink_conf}")
        # Generate Sink DML
        sink_ddl = FlinkService._generate_sink_dml(
            source_conf=source_conf,
            source_conn=source_conn,
            sink_conf=sink_conf,
            sink_conn=sink_conn,
            flink_sink_table_name=flink_sink_table_name,
            flink_sink_config=flink_sink_config,
            unique_keys=unique_keys,
            datasource_transform_ddl=datasource_transform_ddl,
        )
        return set_job_name, source_ddl, sink_ddl, insert_dml

    @staticmethod
    def _validate_source_table_exists(conn: ConnectionItem, source_conf: SourceConfig) -> None:
        """
        Validate that the source table exists in the database.
        If not, raise an exception with suggestions for correct table names.

        Args:
            conn: Source connection item
            source_conf: Source configuration

        Raises:
            RecurveException: If table is not found, with suggestions for available tables
        """
        if source_conf.source_type == SOURCE_TYPE_POSTGRES:
            database_name = source_conf.schema_name
        else:
            database_name = source_conf.database_name

        # Get list of available tables
        try:
            tables_result = ConnectionService.list_tables(
                connection_type=conn.type,
                connection_config=conn.data,
                database=database_name,
            )
            available_tables = [table.name for table in tables_result.items]
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            # If we can't list tables, we'll skip validation and let the columns fetch fail
            return

        # Check if the source table exists
        source_table_name = source_conf.table_name
        if source_table_name not in available_tables:
            # Find similar table names for suggestions (using simple string matching)
            suggestions = []
            source_lower = source_table_name.lower()

            # Partial matches
            for table in available_tables:
                if source_lower in table.lower() or table.lower() in source_lower:
                    suggestions.append(table)

            # If still no suggestions, just show first few available tables
            if not suggestions and available_tables:
                suggestions = available_tables[:5]

            logger.error(
                f"Table '{source_table_name}' not found in database '{database_name}'. "
                f"Available tables: {available_tables[:10]}"
            )

            raise RecurveException(
                code=ERR.STREAM_OPERATOR_TABLE_NOT_FOUND,
                data={
                    "error": "Table not found in database/schema",
                    "table_name": source_conf.table_name,
                    "schema_name": source_conf.schema_name,
                    "database_name": source_conf.database_name,
                    "suggested_tables": suggestions,
                    "available_tables_count": len(available_tables),
                },
            )

    @staticmethod
    async def _fetch_source_columns(conn: ConnectionItem, source_conf: SourceConfig) -> list[ColumnItem]:
        if source_conf.source_type == SOURCE_TYPE_POSTGRES:
            database_name = source_conf.schema_name
        else:
            database_name = source_conf.database_name

        res = ConnectionService.list_columns(
            connection_type=conn.type,
            connection_config=conn.data,
            database_name=database_name,
            table_name=source_conf.table_name,
        )
        logger.info(f"columns: {res.items}, length: {len(res.items)}")
        if not res.items:
            logger.error(
                f"No columns found for table: {source_conf.table_name} in schema: {source_conf.schema_name} of database: {source_conf.database_name}, using {database_name}"
            )
            raise RecurveException(
                code=ERR.STREAM_OPERATOR_NO_COLUMNS_FOUND,
                data={
                    "error": "No columns found for table",
                    "table_name": source_conf.table_name,
                    "schema_name": source_conf.schema_name,
                    "database_name": source_conf.database_name,
                },
            )
        return res.items

    @staticmethod
    async def create_job(payload: CreateJobPayload) -> CreateJobData:
        """
        Create a new Flink CDC job

        Args:
            payload: Job creation payload

        Returns:
            CreateJobResponse with job details
        """
        project_id = payload.project_id
        executor_client: ExecutorClient = ExecutorClient()

        # Build CDC configuration
        source_config = payload.source
        sink_config = payload.sink
        transform_config = payload.transform

        logger.info(f"payload config sent from server: {payload.model_dump()}")

        # Build Source configuration
        source_conn = FlinkService._get_connection_by_name(project_id, source_config.connection_name, executor_client)
        source_ds = FlinkService._convert_connection_to_datasource(source_conn)
        if not source_config.database_name:
            logger.info(f"source_config.database_name is not set, setting it to {source_conn.database}")
            source_config.database_name = source_conn.database

        if not source_config.schema_name:
            logger.info(f"source_config.schema_name is not set, setting it to {source_conn.database_schema}")
            source_config.schema_name = source_conn.database_schema

        # Slot name should be generated by the caller (recurve-server) for PostgreSQL sources
        if source_ds.ds_type == SOURCE_TYPE_POSTGRES:
            if source_config.slot_name:
                logger.info(f"Using PostgreSQL replication slot name: {source_config.slot_name}")
            else:
                logger.error("PostgreSQL source_config.slot_name is not set. It should be generated by the caller.")

        logger.info(f"source_config after validation: {source_config.model_dump()}")

        # Build Sink configuration
        dest_conn = FlinkService._get_connection_by_name(project_id, sink_config.connection_name, executor_client)
        dest_datasource = FlinkService._convert_connection_to_datasource(dest_conn)
        if not sink_config.database_name:
            logger.info(f"sink_config.database_name is not set, setting it to {dest_conn.database}")
            sink_config.database_name = dest_conn.database

        if not sink_config.schema_name:
            logger.info(f"sink_config.schema_name is not set, setting it to {dest_conn.database_schema}")
            sink_config.schema_name = dest_conn.database_schema

        flink_sink_config = build_sink_config_by_datasource(dest_datasource, sink_config)
        logger.info(f"sink_config after validation: {sink_config.model_dump()}")

        # Build Flink CDC configuration
        flink_cdc_config = build_cdc_config_by_datasource(source_ds, source_config)
        logger.info(f"flink_cdc_config after validation: {flink_cdc_config}")

        # Generate Flink SQL DDL
        set_job_name, source_ddl, sink_ddl, insert_dml = await FlinkService._generate_flink_sql_ddl_dml(
            job_name=payload.job_name,
            source_conn=source_conn,
            source_conf=source_config,
            sink_conn=dest_conn,
            sink_conf=sink_config,
            flink_cdc_config=flink_cdc_config,
            flink_sink_config=flink_sink_config,
            transform_config=transform_config,
        )

        # Get Flink connection
        sql_gateway_client = FlinkService._get_flink_sql_gateway_client(
            project_id, payload.flink_config, executor_client
        )

        with sql_gateway_client.get_session() as session_handle:
            for ddl in [set_job_name, source_ddl, sink_ddl]:
                logger.info(f"execute ddl: {ddl}")
                sql_gateway_client.execute_statement(ddl, wait_for_completion=True, session_handle=session_handle)

            logger.info(f"execute insert_dml: {insert_dml}")
            response = sql_gateway_client.execute_statement(
                insert_dml, wait_for_completion=True, session_handle=session_handle
            )
            job_id = response.job_id
            if not job_id:
                raise RecurveException(data=f"Failed to create Flink job: {response}")

            logger.info(f"Successfully created Flink job: {job_id}")

            return CreateJobData(
                job_id=job_id,
                job_name=payload.job_name,
                status=FlinkJobStatus.RUNNING,
                message=SUCCESS_JOB_CREATED,
            )

    # temporary not used
    @staticmethod
    async def _cleanup_postgres_replication_slot(project_id: int, source_config: SourceConfig) -> None:
        """
        Drop PostgreSQL replication slot to free up resources.

        Args:
            project_id: Project ID
            source_config: Source configuration containing connection and slot info
        """
        if not source_config.slot_name:
            logger.warning("No slot_name provided, skipping replication slot cleanup")
            return

        # Get source connection
        source_conn = FlinkService._get_connection_by_name(project_id, source_config.connection_name)

        # Create datasource
        datasource = get_datasource_by_config(
            source_conn.type,
            config=source_conn.data,
            database=source_config.database_name,
            schema=source_config.schema_name,
        )

        slot_name = source_config.slot_name

        # Try to drop the replication slot
        # First check if it exists and is active
        check_sql = f"""
        SELECT active, active_pid
        FROM pg_replication_slots
        WHERE slot_name = '{slot_name}'
        """

        try:
            result = datasource.execute(check_sql)
            if result and len(result) > 0:
                is_active = result[0][0]
                active_pid = result[0][1]

                if is_active:
                    logger.warning(
                        f"Replication slot {slot_name} is still active (PID: {active_pid}). Waiting for it to become inactive..."
                    )
                    # In production, you might want to force terminate the connection
                    # For now, we'll try to drop it anyway and let PostgreSQL handle it

                # Drop the replication slot
                drop_sql = f"SELECT pg_drop_replication_slot('{slot_name}')"
                datasource.execute(drop_sql)
                logger.info(f"Successfully dropped replication slot: {slot_name}")
            else:
                logger.info(f"Replication slot {slot_name} does not exist, nothing to clean up")
        except Exception as e:
            # If slot is still active or doesn't exist, log but don't fail
            error_msg = str(e).lower()
            if "does not exist" in error_msg:
                logger.info(f"Replication slot {slot_name} already removed or never existed")
            elif "is active" in error_msg or "still active" in error_msg:
                logger.warning(
                    f"Replication slot {slot_name} is still active, cannot drop yet. It will be cleaned up later."
                )
            else:
                raise

    @staticmethod
    async def cancel_job(payload: CancelJobPayload) -> str:
        """
        Cancel a running Flink job and clean up resources (e.g., PostgreSQL replication slots)

        Args:
            payload: Job cancellation payload

        Returns:
            CancelJobResponse with cancellation status
        """
        # Cancel job via REST API
        client = FlinkService._get_flink_rest_client(
            project_id=payload.project_id,
            flink_connection_name=payload.flink_connection_name,
        )
        client.cancel_job(payload.job_id)
        logger.info(f"Successfully canceled Flink job: {payload.job_id}")

        # # Clean up PostgreSQL replication slot if this is a PostgreSQL CDC job
        # if payload.source_config and payload.source_config.source_type == SOURCE_TYPE_POSTGRES:
        #     slot_name = payload.source_config.slot_name
        #     if slot_name:
        #         logger.info(f"Cleaning up PostgreSQL replication slot: {slot_name}")
        #         try:
        #             await FlinkService._cleanup_postgres_replication_slot(
        #                 project_id=payload.project_id,
        #                 source_config=payload.source_config,
        #             )
        #             logger.info(f"Successfully dropped PostgreSQL replication slot: {slot_name}")
        #         except Exception as e:
        #             # Log warning but don't fail the cancel operation
        #             logger.warning(f"Failed to drop PostgreSQL replication slot {slot_name}: {e}")

        return "Successfully canceled Flink job"

    @staticmethod
    async def get_job_details(project_id: int, flink_connection_name: str, job_id: str) -> JobDetails:
        """
        Get detailed information about a Flink job

        Args:
            job_id: Flink job ID

        Returns:
            GetJobStatusResponse with job details
        """
        client = FlinkService._get_flink_rest_client(project_id, flink_connection_name)
        job_info = client.get_job_details(job_id)

        if not job_info:
            raise RecurveException(data=ERROR_JOB_NOT_FOUND)

        # Get additional metrics and checkpoints
        exceptions = client.get_job_exceptions(job_id)

        # Build JobDetails object
        job_details = JobDetails(
            job_id=job_id,
            job_name=job_info.get("name", "Unknown"),
            status=FlinkJobStatus(job_info["state"]),
            start_time=datetime.fromtimestamp(job_info.get("start-time", 0) / 1000),
            end_time=datetime.fromtimestamp(job_info.get("end-time", 0) / 1000) if job_info.get("end-time") else None,
            duration=job_info.get("duration"),
            parallelism=job_info.get("parallelism", 0),
            exceptions=exceptions,
        )

        return job_details

    @staticmethod
    async def list_jobs(project_id: int, flink_connection_name: str) -> list[JobSummary]:
        """
        List all Flink jobs, optionally filtered by project

        Args:
            project_id: Optional project ID filter

        Returns:
            GetJobsResponse with job summaries
        """
        client = FlinkService._get_flink_rest_client(project_id, flink_connection_name)
        # Get all jobs from REST API
        jobs_response = client.list_jobs()
        jobs = jobs_response.get("jobs", [])

        job_summaries = []
        for job in jobs:
            job_summary = JobSummary(
                job_id=job["id"],
                job_name=job.get("name", "Unknown"),
                status=FlinkJobStatus(job["status"]),
                start_time=datetime.fromtimestamp(job.get("start-time", 0) / 1000),
                duration=job.get("duration"),
            )
            job_summaries.append(job_summary)

        return job_summaries
