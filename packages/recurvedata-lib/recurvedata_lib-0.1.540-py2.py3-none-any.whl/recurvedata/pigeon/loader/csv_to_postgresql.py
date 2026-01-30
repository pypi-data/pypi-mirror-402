from recurvedata.pigeon import const
from recurvedata.pigeon.connector import new_postgresql_connector
from recurvedata.pigeon.loader.base import BaseLoader, CSVToDBAPIMixin
from recurvedata.pigeon.utils import ensure_query_list, ensure_str_list, fs

allowed_modes = (const.LOAD_RENAME_OVERWRITE, const.LOAD_OVERWRITE, const.LOAD_MERGE, const.LOAD_APPEND)


class CSVToPostgresqlLoader(BaseLoader, CSVToDBAPIMixin):
    def __init__(
        self,
        database,
        table,
        filename,
        connector=None,
        schema=None,
        create_table_ddl=None,
        mode=const.LOAD_OVERWRITE,
        primary_keys=None,
        using_insert=False,
        insert_batch_size=1000,
        insert_concurrency=1,
        delete_file=False,
        dedup=False,
        dedup_uniq_keys=None,
        dedup_orderby=None,
        pre_queries=None,
        post_queries=None,
        *args,
        **kwargs,
    ):
        """Loads a csv file into a Redshift table. Internally using a S3 bucket.

        :param database: the target database name
        :type database: str
        :param table: target table name, should not contains database portion
        :type table: str
        :param filename: the absolute path to csv file
        :type filename: str
        :param connector: a PostgresConnector object used to query PG
        :type connector: pigeon.connector.PostgresConnector
        :param create_table_ddl: create table
        :type create_table_ddl: str
        :param mode: one of (LOAD_OVERWRITE, LOAD_MERGE, LOAD_APPEND)
        :param primary_keys: columns that identifies a unique row, e.g. ['dt', 'product_id'].
                             Required if mode is LOAD_MERGE
        :type primary_keys: list
        :param delete_file: delete the CSV file after loading, default is True
        :type delete_file: bool
        :param dedup: remove duplicated records from staging table before being merged into target
        :type dedup: bool
        :param dedup_uniq_keys: columns that identifies a unique row.
        :type dedup_uniq_keys: list
        :param dedup_orderby: determine which row should be kept.
                              e.g. "to keep the row has minimal timestamp", then set `dedup_orderby='timestamp ASC'
        :param pre_queries: queries executed before loading
        :type pre_queries: list | str
        :param post_queries: queries after loading
        :type post_queries: list | str
        """
        self.database = database

        if "." in table:
            self.schema, self.table = table.split(".")
        else:
            self.schema = schema or "public"
            self.table = table

        if connector is None:
            connector = new_postgresql_connector(database=self.database)
        else:
            connector.database = self.database
        self.connector = connector

        self.filename = filename
        self.create_table_ddl = create_table_ddl

        if mode not in allowed_modes:
            raise ValueError("mode should be one of ({})".format(allowed_modes))

        self.mode = mode
        self.primary_keys = ensure_str_list(primary_keys)
        if self.mode == const.LOAD_MERGE and not self.primary_keys:
            raise ValueError("primary_keys should not be empty in mode {}".format(const.LOAD_MERGE))

        self.using_insert = using_insert
        self.insert_batch_size = insert_batch_size
        self.insert_concurrency = insert_concurrency
        self.delete_file = delete_file

        self.dedup = dedup
        self.dedup_uniq_keys = ensure_str_list(dedup_uniq_keys)
        self.dedup_orderby = dedup_orderby
        if self.dedup and not self.dedup_uniq_keys:
            raise ValueError("dedup_uniq_keys should not be empty")
        if not self.dedup_orderby:
            self.dedup_orderby = ", ".join(self.dedup_uniq_keys)

        self.pre_queries = ensure_query_list(pre_queries) or []
        self.post_queries = ensure_query_list(post_queries) or []

        super().__init__()

    def execute_impl(self):
        if fs.is_file_empty(self.filename):
            self.logger.error("file not exists or has no content. %s", self.filename)
            fs.remove_files_safely(fs.schema_filename(self.filename))
            return
        self._prepare_target_table()
        self._prepare_staging_table()
        self._merge_into_target_table()

        # do cleaning things
        if self.delete_file:
            self.logger.info("delete local file %s", self.filename)
            fs.remove_files_safely(self.filename)
            fs.remove_files_safely(fs.schema_filename(self.filename))

    @property
    def full_table_name(self):
        return f"{self.schema}.{self.table}"

    @property
    def staging_table(self):
        return f"{self.schema}.{self.table}_staging"

    @property
    def bak_table(self):
        return f"{self.schema}.{self.table}_bak"

    def _prepare_staging_table(self):
        queries = """
            DROP TABLE IF EXISTS {st};
            CREATE TABLE {st} (LIKE {ft});
        """.format(
            st=self.staging_table, ft=self.full_table_name
        )
        self.connector.execute(queries, autocommit=True)

        self.connector.load_csv(
            table=self.staging_table,
            filename=self.filename,
            using_insert=self.using_insert,
            null_values=("NULL", r"\N", ""),
            batch_size=self.insert_batch_size,
            concurrency=self.insert_concurrency,
        )

        if self.dedup:
            dedup_query = self._construct_dedup_query(partition_keys=self.dedup_uniq_keys, order_by=self.dedup_orderby)
            self.connector.execute(dedup_query, autocommit=False)

    def _construct_dedup_query(self, partition_keys=None, order_by=None):
        """Construct deduplication query with specified partition keys and order by clause"""
        if partition_keys is None:
            partition_keys = self.dedup_uniq_keys
        if order_by is None:
            order_by = self.dedup_orderby

        partition_cols = []
        for col in partition_keys:
            partition_cols.append(self.connector.quote_identifier(col))
        partition_by = ", ".join(partition_cols)

        cols = self.connector.get_columns(self.staging_table)
        tmp_table = f"{self.staging_table}_tmp"

        query = f"""
            DROP TABLE IF EXISTS {tmp_table};
            CREATE TABLE {tmp_table} AS
            SELECT {', '.join(self.connector.quote_identifier(x) for x in cols)}
            FROM (
              SELECT *, ROW_NUMBER() OVER(PARTITION BY {partition_by} ORDER BY {order_by}) AS rn
              FROM {self.staging_table}
            ) t
            WHERE rn = 1;

            TRUNCATE TABLE {self.staging_table};
            INSERT INTO {self.staging_table} SELECT * FROM {tmp_table};
            DROP TABLE IF EXISTS {tmp_table};
        """
        return query

    def _merge_into_target_table(self):
        queries = []
        pure_bak_table = self.bak_table.split(".")[-1]
        pure_full_table = self.full_table_name.split(".")[-1]
        if self.mode == const.LOAD_OVERWRITE:
            queries.append(f"DROP TABLE IF EXISTS {self.bak_table}")
            queries.append(f"ALTER TABLE {self.full_table_name} RENAME TO {pure_bak_table}")
            queries.append(f"ALTER TABLE {self.staging_table} RENAME TO {pure_full_table}")
            queries.append(f"DROP TABLE IF EXISTS {self.bak_table}")
        elif self.mode == const.LOAD_MERGE:
            # Deduplicate staging table data before merging using primary_keys
            # Use primary_keys order for ordering
            order_by = ", ".join(self.connector.quote_identifier(col) for col in self.primary_keys)
            dedup_query = self._construct_dedup_query(partition_keys=self.primary_keys, order_by=order_by)
            queries.append(dedup_query)

            joins = []
            for field in self.primary_keys:
                join = "{target}.{field} = {staging}.{field}".format(
                    target=self.full_table_name, staging=self.staging_table, field=field
                )
                joins.append(join)

            join_conditions = " AND ".join(joins)
            delete_sql = "DELETE FROM {target} USING {staging} WHERE {join_conditions}".format(
                target=self.full_table_name, staging=self.staging_table, join_conditions=join_conditions
            )
            queries.append(delete_sql)

            # Insert data from staging table to target table
            insert_sql = "INSERT INTO {target} SELECT * FROM {source}".format(
                target=self.full_table_name, source=self.staging_table
            )
            queries.append(insert_sql)
            queries.append("DROP TABLE {}".format(self.staging_table))
        else:
            # else APPEND
            append_sql = "INSERT INTO {target} SELECT * FROM {source}".format(
                target=self.full_table_name, source=self.staging_table
            )
            queries.append(append_sql)
            queries.append("DROP TABLE {}".format(self.staging_table))

        queries = self.pre_queries + queries + self.post_queries
        self.logger.info("running PostgreSQL queries...")
        try:
            self.connector.execute(queries, autocommit=False, commit_on_close=True)
        except Exception as e:
            self.logger.exception("failed to run queries")
            raise e
        finally:
            if (
                self.mode == const.LOAD_OVERWRITE
                and not self.connector.has_table(self.full_table_name)
                and self.connector.has_table(self.bak_table)
            ):
                rename_sql = "ALTER TABLE {} RENAME TO {}".format(self.bak_table, pure_full_table)
                self.connector.execute(rename_sql, autocommit=False, commit_on_close=True)

        try:
            self.logger.info("running analyze")
            analyze_queries = "VACUUM {t}; ANALYZE {t}".format(t=self.full_table_name)
            self.connector.execute(analyze_queries, autocommit=True)
        except Exception as e:
            self.logger.exception(f"failed to run analyze queries: {e}")
