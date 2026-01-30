from recurvedata.pigeon import const
from recurvedata.pigeon.connector import new_mysql_connector
from recurvedata.pigeon.csv import CSV
from recurvedata.pigeon.loader.base import BaseLoader, CSVToDBAPIMixin
from recurvedata.pigeon.utils import ensure_query_list, ensure_str_list, fs
from recurvedata.pigeon.utils.sql import bak_table_of, staging_table_of

allowed_modes = (const.LOAD_OVERWRITE, const.LOAD_MERGE, const.LOAD_APPEND)


class CSVToMySQLLoader(BaseLoader, CSVToDBAPIMixin):
    def __init__(
        self,
        database,
        table,
        filename,
        connector=None,
        create_table_ddl=None,
        mode=const.LOAD_OVERWRITE,
        primary_keys=None,
        skiprows=0,
        columns=None,
        using_insert=False,
        insert_batch_size=1000,
        insert_concurrency=1,
        delete_file=False,
        tidb_dml_batch_size=500,
        pre_queries=None,
        post_queries=None,
        *args,
        **kwargs,
    ):
        self.database = database
        self.table = table

        if isinstance(filename, CSV):
            filename = filename.path
        self.filename = filename
        self.csvfile = CSV(self.filename)

        if connector is None:
            connector = new_mysql_connector(database=self.database)
        else:
            connector.database = self.database
        self.connector = connector

        self.create_table_ddl = create_table_ddl

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

        # https://pingcap.com/docs-cn/sql/tidb-specific/#tidb-dml-batch-size
        self.tidb_dml_batch_size = tidb_dml_batch_size

        self.pre_queries = ensure_query_list(pre_queries) or []
        self.post_queries = ensure_query_list(post_queries) or []

        super().__init__()

    @property
    def staging_table(self):
        return staging_table_of(self.table)

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
        queries = """
            DROP TABLE IF EXISTS {staging};
            CREATE TABLE {staging} LIKE {table};
        """.format(
            staging=self.staging_table, table=self.table
        )
        self.connector.execute(queries, autocommit=True)

    def _load_to_staging(self):
        self.connector.load_csv(
            table=self.staging_table,
            filename=self.csvfile.path,
            columns=self.columns,
            lineterminator=self.csvfile.dialect.lineterminator,
            skiprows=self.skiprows,
            using_insert=self.using_insert,
            null_values=("NULL", r"\N", ""),
            batch_size=self.insert_batch_size,
            concurrency=self.insert_concurrency,
        )

    def _merge_into_target_table(self):
        queries = []
        if self.connector.is_tidb():
            queries.append("SET autocommit=1")
            queries.append("SET @@session.tidb_batch_delete=ON")
            queries.append("SET @@session.tidb_batch_insert=ON")
            if self.tidb_dml_batch_size:
                queries.append(f"SET @@session.tidb_dml_batch_size={self.tidb_dml_batch_size}")

        if self.mode == const.LOAD_MERGE:
            queries.extend(self._ingest_by_merging())
        elif self.mode == const.LOAD_OVERWRITE:
            bak_table = bak_table_of(self.table)
            queries.append(f"DROP TABLE IF EXISTS {bak_table}")
            queries.append(f"RENAME TABLE {self.table} TO {bak_table}")
            queries.append(f"RENAME TABLE {self.staging_table} TO {self.table}")
            queries.append(f"DROP TABLE IF EXISTS {bak_table}")
        else:
            queries.append(f"INSERT INTO {self.table} SELECT * FROM {self.staging_table}")
            queries.append(f"DROP TABLE {self.staging_table}")

        queries = self.pre_queries + queries + self.post_queries
        self.logger.info("running MySQL queries within a transaction")
        self.connector.execute(queries, autocommit=False, commit_on_close=True)

    def _ingest_by_merging(self):
        """Merge with deduplication based on specified primary_keys"""
        # First, deduplicate staging table based on primary_keys using window function
        pk_columns = ", ".join(self.primary_keys)

        # Get all columns from staging table (excluding the rn column we'll add)
        cols = self.connector.get_columns(self.staging_table)
        cols_str = ", ".join(self.connector.quote_identifier(x) for x in cols)

        # Create a temporary table with deduplicated data
        tmp_table = f"{self.staging_table}_dedup"
        dedup_sql = f"""
            DROP TABLE IF EXISTS {tmp_table};
            CREATE TABLE {tmp_table} LIKE {self.staging_table};
            INSERT INTO {tmp_table}
            SELECT {cols_str} FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY {pk_columns} ORDER BY {pk_columns}) AS rn
                FROM {self.staging_table}
            ) t
            WHERE rn = 1;
        """

        # Replace staging table with deduplicated data
        replace_sql = f"""
            DROP TABLE {self.staging_table};
            RENAME TABLE {tmp_table} TO {self.staging_table};
        """

        # Delete records from target table that have the same primary keys as staging table
        join_condition = " AND ".join([f"a.{pk} = b.{pk}" for pk in self.primary_keys])
        delete_sql = f"""
            DELETE a FROM {self.table} a
            INNER JOIN {self.staging_table} b ON {join_condition}
        """

        # Insert deduplicated data into target table
        insert_sql = f"INSERT INTO {self.table} SELECT * FROM {self.staging_table}"
        drop_sql = f"DROP TABLE {self.staging_table}"

        return [dedup_sql, replace_sql, delete_sql, insert_sql, drop_sql]
