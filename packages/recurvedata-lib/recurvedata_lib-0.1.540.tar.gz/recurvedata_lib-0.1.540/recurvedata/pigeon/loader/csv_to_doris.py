from typing import TYPE_CHECKING, Any, List, Optional

from recurvedata.pigeon import const
from recurvedata.pigeon.loader.csv_to_mysql import CSVToMySQLLoader
from recurvedata.pigeon.utils import md5hash
from recurvedata.pigeon.utils.sql import bak_table_of, reconcile_table_of, staging_table_of

if TYPE_CHECKING:
    from recurvedata.pigeon.connector.doris import DorisConnector

allowed_modes = (const.LOAD_OVERWRITE, const.LOAD_MERGE, const.LOAD_APPEND)


class CSVToDorisLoader(CSVToMySQLLoader):
    def __init__(
        self,
        database: str,
        table: str,
        filename: str,
        connector: Optional["DorisConnector"] = None,
        create_table_ddl: Optional[str] = None,
        mode: str = const.LOAD_OVERWRITE,
        primary_keys: Optional[List[str]] = None,
        skiprows: int = 0,
        columns: Optional[List[str]] = None,
        using_insert: bool = False,
        insert_batch_size: int = 1000,
        insert_concurrency: int = 1,
        delete_file: bool = False,
        pre_queries: Optional[List[str]] = None,
        post_queries: Optional[List[str]] = None,
        load_strict_mode: bool = False,
        max_filter_ratio: float = 0,
        *args: Any,
        **kwargs: Any,
    ):
        if not connector:
            raise ValueError(f"connector is required for {self.__class__.__name__}")
        self.load_strict_mode: bool = load_strict_mode
        connector.load_strict_mode = load_strict_mode
        self.logger.info(f"load_strict_mode: {load_strict_mode}")
        connector.max_filter_ratio = max_filter_ratio
        self.logger.info(f"max_filter_ratio: {max_filter_ratio}")
        table_suffix: str = md5hash(filename)[:6]
        self.__staging_table: str = staging_table_of(table) + "_" + table_suffix
        self.__reconcile_table: str = reconcile_table_of(table) + "_" + table_suffix
        self.__bak_table: str = bak_table_of(table) + "_" + table_suffix

        # Check table name length
        if any(
            [
                len(self.__staging_table) > 64,
                len(self.__reconcile_table) > 64,
                len(self.__bak_table) > 64,
            ]
        ):
            self.logger.error(
                f"table name {self.__staging_table} 's length: {len(self.__staging_table)}\n"
                f"table name {self.__reconcile_table}'s length: {len(self.__reconcile_table)}\n"
                f"table name {self.__bak_table}'s length: {len(self.__bak_table)}\n"
            )
            raise ValueError("length of intermediate table name is greater than 64!")

        super().__init__(
            database=database,
            table=table,
            filename=filename,
            connector=connector,
            create_table_ddl=create_table_ddl,
            mode=mode,
            primary_keys=primary_keys,
            skiprows=skiprows,
            columns=columns,
            using_insert=using_insert,
            insert_batch_size=insert_batch_size,
            insert_concurrency=insert_concurrency,
            delete_file=delete_file,
            pre_queries=pre_queries,
            post_queries=post_queries,
            *args,
            **kwargs,
        )

    @property
    def staging_table(self) -> str:
        """
        Override method to return table name with random suffix
        """
        return self.__staging_table

    def _merge_into_target_table(self) -> None:
        queries = []
        if self.mode == const.LOAD_MERGE:
            queries.extend(self._ingest_by_merging())
        elif self.mode == const.LOAD_OVERWRITE:
            bak_table = self.__bak_table
            queries.extend(
                [
                    f"DROP TABLE IF EXISTS {bak_table}",
                    f"ALTER TABLE {self.table} RENAME {bak_table}",
                    f"ALTER TABLE {self.staging_table} RENAME {self.table}",
                    f"DROP TABLE IF EXISTS {bak_table}",
                ]
            )
        else:  # APPEND mode
            queries.append(f"INSERT INTO {self.table} SELECT * FROM {self.staging_table}")
            self.connector.execute(self.pre_queries + queries, autocommit=True, commit_on_close=False)

            queries.clear()
            queries.append(f"DROP TABLE {self.staging_table}")
            self.connector.execute(queries + self.post_queries, autocommit=True, commit_on_close=False)
            return

        queries = self.pre_queries + queries + self.post_queries
        self.logger.info("running MySQL queries within a transaction")
        self.connector.execute(queries, autocommit=False, commit_on_close=True)

    def _ingest_by_merging(self) -> List[str]:
        """Merge with deduplication based on primary keys using Doris-compatible syntax"""
        # First, deduplicate staging table based on primary keys using window function
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
            ALTER TABLE {tmp_table} RENAME {self.staging_table};
        """

        # Simple merge: backup target table, then merge and deduplicate in one step
        bak = self.__bak_table
        table = self.connector.quote_identifier(self.table)
        staging = self.connector.quote_identifier(self.staging_table)
        bak = self.connector.quote_identifier(bak)

        # Simple and efficient merge: backup + merge + deduplicate in one operation
        merge_sql = f"""
            -- Backup target table
            DROP TABLE IF EXISTS {bak};
            ALTER TABLE {table} RENAME {bak};

            -- Create new target table and insert deduplicated merged data in one step
            CREATE TABLE {table} AS
            SELECT {cols_str} FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY {pk_columns} ORDER BY {pk_columns}) AS rn
                FROM (
                    SELECT * FROM {bak}
                    UNION ALL
                    SELECT * FROM {staging}
                ) combined
            ) t WHERE rn = 1;

            -- Clean up
            DROP TABLE {bak};
            DROP TABLE {staging};
        """

        return [dedup_sql, replace_sql, merge_sql]

    def execute(self) -> None:
        """
        Override method to implement exception handling
        """
        self.before_execute()
        try:
            self.execute_impl()
        except Exception as e:
            self.handle_exception()
            raise e
        self.after_execute()

    def handle_exception(self) -> None:
        """
        Ensure safe cleanup of all intermediate tables after an exception occurs
        """
        qry_exists_sql = """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = '{database}' AND table_name = '{table}';
        """
        is_table_exists = self.connector.fetchall(qry_exists_sql.format(database=self.database, table=self.table))
        is_bak_exists = self.connector.fetchall(qry_exists_sql.format(database=self.database, table=self.__bak_table))

        if is_table_exists:
            # Directly clean up intermediate tables
            queries = [
                f"DROP TABLE IF EXISTS {self.__bak_table}",
                f"DROP TABLE IF EXISTS {self.__staging_table}",
                f"DROP TABLE IF EXISTS {self.__reconcile_table}",
            ]
        elif is_bak_exists:
            # Restore from backup table
            queries = [
                f"ALTER TABLE {self.__bak_table} RENAME {self.table}",
                f"DROP TABLE IF EXISTS {self.__staging_table}",
                f"DROP TABLE IF EXISTS {self.__reconcile_table}",
            ]
        else:
            queries = [f"DROP TABLE IF EXISTS {self.__staging_table}", f"DROP TABLE IF EXISTS {self.__reconcile_table}"]
        self.connector.execute(queries, autocommit=False, commit_on_close=True)
