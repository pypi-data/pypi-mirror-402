from typing import TYPE_CHECKING, Any, List, Optional, Union

from recurvedata.pigeon import const
from recurvedata.pigeon.loader.base import BaseLoader, CSVToDBAPIMixin
from recurvedata.pigeon.utils import ensure_query_list, ensure_str_list, fs

if TYPE_CHECKING:
    from recurvedata.pigeon.connector.microsoft_fabric import MsFabricConnector

allowed_modes = (const.LOAD_OVERWRITE, const.LOAD_MERGE, const.LOAD_APPEND)


class CSVToMsFabricLoader(BaseLoader, CSVToDBAPIMixin):
    """Loader for Microsoft Fabric that supports bulk loading data using COPY command.

    This loader provides Microsoft Fabric specific data loading capabilities.
    It uses the COPY command for efficient data loading and supports various
    loading modes (OVERWRITE, MERGE, APPEND).
    """

    def __init__(
        self,
        table: str,
        filename: str,
        connector: "MsFabricConnector",
        schema: Optional[str] = None,
        create_table_ddl: Optional[str] = None,
        mode: str = const.LOAD_MERGE,
        primary_keys: Optional[Union[str, List[str]]] = None,
        columns: Optional[Union[str, List[str]]] = None,
        compress: bool = True,
        delete_file: bool = True,
        dedup: bool = False,
        dedup_uniq_keys: Optional[Union[str, List[str]]] = None,
        dedup_orderby: Optional[Union[str, List[str]]] = None,
        pre_queries: Optional[Union[str, List[str]]] = None,
        post_queries: Optional[Union[str, List[str]]] = None,
        lineterminator: Optional[str] = "0x0D0A",
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the loader.

        Args:
            table: Target table name
            filename: Source file path
            connector: MsFabricConnector instance
            schema: Schema name
            create_table_ddl: SQL to create target table
            mode: Loading mode (OVERWRITE/MERGE/APPEND)
            primary_keys: Primary key columns for MERGE mode
            columns: Column list to load
            compress: Whether to compress data before loading
            delete_file: Whether to delete source file after loading
            dedup: Whether to deduplicate data
            dedup_uniq_keys: Columns for deduplication
            dedup_orderby: Order by clause for deduplication
            pre_queries: Queries to run before loading
            post_queries: Queries to run after loading
        """
        if "." in table:
            self.schema, self.table = table.split(".")
        else:
            self.schema = schema or "dbo"
            self.table = table

        self.connector = connector
        self.filename = filename
        self.create_table_ddl = create_table_ddl
        self.compress = compress
        self.delete_file = delete_file

        if mode not in allowed_modes:
            raise ValueError(f"mode should be one of ({allowed_modes})")

        self.mode = mode
        self.primary_keys = ensure_str_list(primary_keys)
        self.columns = ensure_str_list(columns)

        # dedup stuff
        self.dedup = dedup
        self.dedup_uniq_keys = ensure_str_list(dedup_uniq_keys)
        self.dedup_orderby = dedup_orderby
        if self.dedup and not self.dedup_uniq_keys:
            raise ValueError("dedup_uniq_keys should not be empty if dedup is true")

        self.pre_queries = ensure_query_list(pre_queries) or []
        self.post_queries = ensure_query_list(post_queries) or []
        self.lineterminator = lineterminator

        super().__init__()

    @property
    def staging_table(self) -> str:
        return f"{self.table}_staging"

    @property
    def full_staging_table_name(self) -> str:
        return f"{self.schema}.{self.staging_table}"

    @property
    def full_table_name(self) -> str:
        return f"{self.schema}.{self.table}"

    @property
    def quoted_full_staging_table(self) -> str:
        return self.connector.quote_identifier(self.full_staging_table_name)

    @property
    def quoted_full_table_name(self) -> str:
        return self.connector.quote_identifier(self.full_table_name)

    def execute_impl(self) -> None:
        """Execute the data loading process."""
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

    def _prepare_staging_table(self) -> None:
        """Prepare the staging table for data loading."""
        schema, table = self.full_staging_table_name.split(".")
        drop = self._make_drop_table_query(schema, table)
        ddl = f"SELECT TOP 0 * INTO {self.quoted_full_staging_table} FROM {self.quoted_full_table_name}"
        self.connector.execute([drop, ddl])

    def _make_drop_table_query(self, schema: str, table: str) -> str:
        """Generate SQL to drop a table if it exists."""
        if "." in table:
            schema, table = table.split(".")
        if not schema:
            schema = self.schema
        full_table = f"{schema}.{table}"
        query = f"""
            IF EXISTS (
              SELECT * FROM sys.tables
              WHERE schema_name(schema_id) = '{schema}' AND name = '{table}'
            )
            DROP TABLE {self.connector.quote_identifier(full_table)}
        """
        return query

    def _load_to_staging(self) -> None:
        """Load data into staging table using COPY command."""
        self.logger.info(f"load {self.filename} into staging table {self.full_staging_table_name}")
        self.connector.load_csv_bulk(
            table=self.full_staging_table_name,
            filename=self.filename,
            columns=self.columns,
            compress=self.compress,
            lineterminator=self.lineterminator,
        )

        if self.dedup:
            dedup_query = self._construct_dedup_query()
            self.connector.execute(dedup_query, autocommit=False, commit_on_close=True)

    def _construct_dedup_query(self) -> str:
        """Construct query for deduplication."""
        partitions_cols = []
        for col in self.dedup_uniq_keys:
            partitions_cols.append(self.connector.quote_identifier(col))
        partition_by = ", ".join(partitions_cols)
        columns = " ,".join(self.connector.get_columns(schema=self.schema, table=self.staging_table))
        tmp_table = f"{self.full_staging_table_name}_tmp"
        quoted_tmp_table = self.connector.quote_identifier(tmp_table)
        quoted_bak_table = self.connector.quote_identifier(f"{self.staging_table}_bak")

        queries = f"""
            {self._make_drop_table_query(self.schema, tmp_table)};

            CREATE TABLE {quoted_tmp_table} AS
            SELECT {', '.join(self.connector.quote_identifier(x) for x in columns)}
            FROM (
              SELECT *, ROW_NUMBER() OVER (PARTITION BY {partition_by} ORDER BY {self.dedup_orderby}) rn
              FROM {self.quoted_full_staging_table}
            ) AS t
            WHERE rn = 1;

            RENAME OBJECT {self.quoted_full_staging_table} TO {quoted_bak_table};
            RENAME OBJECT {quoted_tmp_table} TO {self.staging_table};
            DROP TABLE {quoted_bak_table};
        """
        return queries

    def _merge_into_target_table(self) -> None:
        """Merge data from staging table into target table."""
        target = self.quoted_full_table_name
        staging = self.quoted_full_staging_table

        append_sql = f"INSERT INTO {target} SELECT * FROM {staging}"
        if self.mode == const.LOAD_OVERWRITE:
            queries = [f"TRUNCATE TABLE {target}", append_sql]
        elif self.mode == const.LOAD_MERGE:
            queries = self._ingest_by_merging()
        else:
            # APPEND
            queries = [append_sql]

        queries.append(f"DROP TABLE {staging}")

        queries = self.pre_queries + queries + self.post_queries
        self.logger.info("running Microsoft Fabric queries...")
        self.connector.execute(queries, autocommit=True, commit_on_close=True)
        self.logger.info("done.")

    def _ingest_by_merging(self) -> List[str]:
        """Construct merge query for MERGE mode."""
        merge_table = f"{self.full_table_name}_merge"
        quote = self.connector.quote_identifier
        join = " AND ".join([f"a.{quote(x)} = b.{quote(x)}" for x in self.primary_keys])

        drop_merge_table = self._make_drop_table_query(self.schema, merge_table)
        queries = f"""
            {drop_merge_table};

            CREATE TABLE {quote(merge_table)} WITH (DISTRIBUTION = ROUND_ROBIN)
            AS
            SELECT a.*
            FROM {self.quoted_full_table_name} AS a
            LEFT JOIN {self.quoted_full_staging_table} AS b ON {join}
            WHERE b.{quote(self.primary_keys[0])} IS NULL
            UNION ALL
            SELECT * FROM {self.quoted_full_staging_table};

            TRUNCATE TABLE {self.quoted_full_table_name};
            INSERT INTO {self.quoted_full_table_name} SELECT * FROM {quote(merge_table)};

            {drop_merge_table};
        """
        return queries.split(";")
