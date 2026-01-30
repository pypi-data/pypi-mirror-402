from recurvedata.pigeon import const
from recurvedata.pigeon.connector.mssql import SQLServerConnector
from recurvedata.pigeon.loader.base import BaseLoader, CSVToDBAPIMixin
from recurvedata.pigeon.utils import ensure_query_list, ensure_str_list, fs

allowed_modes = (const.LOAD_OVERWRITE, const.LOAD_MERGE, const.LOAD_APPEND)
STATING_TABLE_NAME_PLACEHOLDER = "<TABLE>"


class CSVToMsSQLLoader(BaseLoader, CSVToDBAPIMixin):
    def __init__(
        self,
        database,
        table,
        filename,
        connector: SQLServerConnector,
        schema=None,
        create_table_ddl=None,
        staging_create_table_ddl=None,
        mode=const.LOAD_OVERWRITE,
        primary_keys=None,
        skiprows=0,
        columns=None,
        using_insert=True,
        insert_batch_size=500,
        insert_concurrency=1,
        delete_file=False,
        pre_queries=None,
        post_queries=None,
        *args,
        **kwargs,
    ):
        self.database = database
        self.table = table

        if "." in table:
            self.schema, self.table = table.split(".")
        else:
            self.schema = schema or "dbo"
            self.table = table

        connector.database = self.database
        self.connector = connector
        self.filename = filename
        self.create_table_ddl = create_table_ddl
        # 考虑到完整的复制表结构（包括约束和索引）比较复杂，允许指定 staging 表的 DDL
        # 表名用特殊符号 <TABLE> 占位
        self.staging_create_table_ddl = staging_create_table_ddl
        if self.staging_create_table_ddl and STATING_TABLE_NAME_PLACEHOLDER not in self.staging_create_table_ddl:
            raise ValueError(f"use {STATING_TABLE_NAME_PLACEHOLDER} as table name placeholder")

        if mode not in allowed_modes:
            raise ValueError("mode should be one of ({})".format(allowed_modes))

        self.mode = mode
        self.primary_keys = ensure_str_list(primary_keys)
        if self.mode == const.LOAD_MERGE and not self.primary_keys:
            raise ValueError("primary_keys should not be empty in mode {}".format(const.LOAD_MERGE))

        # self.columns = columns or self.csvfile.header
        # self.skiprows = int(skiprows or self.csvfile.has_header)
        self.columns = columns
        self.skiprows = int(skiprows)
        self.using_insert = using_insert
        self.insert_batch_size = insert_batch_size
        self.insert_concurrency = insert_concurrency
        self.delete_file = delete_file

        self.pre_queries = ensure_query_list(pre_queries) or []
        self.post_queries = ensure_query_list(post_queries) or []

        super().__init__()

    @property
    def staging_table(self):
        return f"{self.schema}.{self.table}_staging"

    @property
    def full_table_name(self):
        return f"{self.schema}.{self.table}"

    @property
    def quoted_staging_table(self):
        return self.connector.quote_identifier(self.staging_table)

    @property
    def quoted_full_table_name(self):
        return self.connector.quote_identifier(self.full_table_name)

    def execute_impl(self):
        if fs.is_file_empty(self.filename):
            self.logger.error("file not exists or has no content. %s", self.filename)
            fs.remove_files_safely(fs.schema_filename(self.filename))
            return

        self._prepare_target_table()
        self._prepare_staging_table()
        self._load_to_staging()
        self._merge_into_target_table()

        # do cleaning things
        if self.delete_file:
            self.logger.info("delete local file %s", self.filename)
            fs.remove_files_safely(self.filename)
            fs.remove_files_safely(fs.schema_filename(self.filename))

    def _prepare_staging_table(self):
        schema, table = self.staging_table.split(".")
        if self.staging_create_table_ddl:
            ddl: str = self.staging_create_table_ddl.replace(STATING_TABLE_NAME_PLACEHOLDER, self.quoted_staging_table)
            ddl = ddl.rstrip(";")
        else:
            ddl = f"SELECT TOP 0 * INTO {self.quoted_staging_table} FROM {self.quoted_full_table_name}"

        query = f"""
            IF EXISTS (
              SELECT * FROM sys.tables
              WHERE schema_name(schema_id) = '{schema}' AND name = '{table}'
            )
            DROP TABLE {self.quoted_staging_table};

            {ddl}
        """
        self.connector.execute(query)

    def _load_to_staging(self):
        self.logger.info("load %s into staging table %s", self.filename, self.staging_table)
        self.connector.load_csv(
            table=self.staging_table,
            filename=self.filename,
            schema=self.schema,
            columns=self.columns,
            skiprows=self.skiprows,
            using_insert=self.using_insert,
            null_values=("NULL", r"\N", ""),
            batch_size=self.insert_batch_size,
            concurrency=self.insert_concurrency,
        )

    def _merge_into_target_table(self):
        target = self.quoted_full_table_name
        staging = self.quoted_staging_table

        queries = []
        if self.mode == const.LOAD_OVERWRITE:
            queries.append(f"TRUNCATE TABLE {target}")
            append_sql = f"INSERT INTO {target} SELECT * FROM {staging}"
            queries.append(append_sql)
        elif self.mode == const.LOAD_MERGE:
            joins = []
            for field in self.primary_keys:
                field = self.connector.quote_identifier(field)
                join = f"{target}.{field} = {staging}.{field}"
                joins.append(join)

            join_conditions = " AND ".join(joins)
            # Delete existing records that match primary keys
            delete_sql = f"DELETE {target} FROM {target} INNER JOIN {staging} ON {join_conditions}"
            queries.append(delete_sql)

            # Insert all data from staging table to target table
            insert_sql = f"INSERT INTO {target} SELECT * FROM {staging}"
            queries.append(insert_sql)
        else:
            # APPEND mode
            append_sql = f"INSERT INTO {target} SELECT * FROM {staging}"
            queries.append(append_sql)

        queries.append(f"DROP TABLE {staging}")

        queries = self.pre_queries + queries + self.post_queries
        self.logger.info("running SQL Server queries...")
        self.connector.execute(queries, autocommit=False, commit_on_close=True)
        self.logger.info("done.")
