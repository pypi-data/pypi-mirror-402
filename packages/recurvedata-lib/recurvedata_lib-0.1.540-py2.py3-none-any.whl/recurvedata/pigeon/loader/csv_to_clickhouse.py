from recurvedata.pigeon import const
from recurvedata.pigeon.connector import new_clickhouse_connector
from recurvedata.pigeon.csv import CSV
from recurvedata.pigeon.loader.base import BaseLoader, CSVToDBAPIMixin
from recurvedata.pigeon.utils import ensure_query_list, ensure_str_list, fs
from recurvedata.pigeon.utils.sql import bak_table_of, reconcile_table_of, staging_table_of

allowed_modes = (const.LOAD_OVERWRITE, const.LOAD_MERGE, const.LOAD_APPEND)


class CSVToClickHouseLoader(BaseLoader, CSVToDBAPIMixin):
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
        using_insert=False,
        insert_batch_size=10000,
        insert_concurrency=1,
        delete_file=False,
        table_engine="Log",
        pre_queries=None,
        post_queries=None,
        native=False,
    ):
        self.database = database
        self.table = table

        if isinstance(filename, CSV):
            filename = filename.path
        self.filename = filename
        self.csvfile = CSV(self.filename)

        if connector is None:
            connector = new_clickhouse_connector(database=self.database, native=native)
        else:
            connector.database = self.database
        self.connector = connector

        self.create_table_ddl = create_table_ddl
        self.ddl_options = {"ENGINE": table_engine}

        if mode not in allowed_modes:
            raise ValueError("mode should be one of ({})".format(allowed_modes))

        self.mode = mode
        self.primary_keys = ensure_str_list(primary_keys)
        if self.mode == const.LOAD_MERGE and not self.primary_keys:
            raise ValueError("primary_keys should not be empty in mode {}".format(const.LOAD_MERGE))

        # self.columns = columns or self.csvfile.header
        # self.skiprows = int(skiprows or self.csvfile.has_header)
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
            CREATE TABLE {staging} AS {table};
        """.format(
            staging=self.staging_table, table=self.table
        )
        self.connector.execute(queries, autocommit=True)

    def _load_to_staging(self):
        self.connector.load_csv(
            table=self.staging_table,
            filename=self.csvfile.path,
            lineterminator=self.csvfile.dialect.lineterminator,
            skiprows=self.skiprows,
            null_values=("NULL", r"\N"),
            using_insert=self.using_insert,
            batch_size=self.insert_batch_size,
            concurrency=self.insert_concurrency,
        )

    def _merge_into_target_table(self):
        queries = []
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
        self.connector.execute(queries)

    def _ingest_by_merging(self):
        reconcile = reconcile_table_of(self.table)
        bak = bak_table_of(self.table)
        using = ", ".join(self.primary_keys)
        sql = """
            DROP TABLE IF EXISTS {reconcile};
            CREATE TABLE {reconcile} AS {table};

            INSERT INTO {reconcile}
            SELECT * FROM {table} WHERE NOT ({using}) IN (SELECT {using} FROM {staging})
            UNION ALL
            SELECT * FROM {staging};

            RENAME TABLE {table} TO {bak};
            RENAME TABLE {reconcile} TO {table};
            DROP TABLE IF EXISTS {bak};
            DROP TABLE {staging};
        """.format(
            reconcile=self.connector.quote_identifier(reconcile),
            table=self.connector.quote_identifier(self.table),
            staging=self.connector.quote_identifier(self.staging_table),
            bak=self.connector.quote_identifier(bak),
            using=using,
        )
        queries = sql.split(";")
        return queries
