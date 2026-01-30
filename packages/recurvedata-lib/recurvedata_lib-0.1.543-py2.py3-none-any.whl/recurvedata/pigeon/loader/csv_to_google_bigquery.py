from typing import TYPE_CHECKING, List, Union

from recurvedata.pigeon import const
from recurvedata.pigeon.loader.base import BaseLoader, CSVToDBAPIMixin
from recurvedata.pigeon.utils import ensure_query_list, ensure_str_list, fs
from recurvedata.pigeon.utils.sql import bak_table_of, reconcile_table_of, staging_table_of

if TYPE_CHECKING:
    from recurvedata.pigeon.connector.google_bigquery import GoogleBigqueryConnector

allowed_modes = (
    const.LOAD_OVERWRITE,
    const.LOAD_MERGE,
    const.LOAD_APPEND
)


class CSVToGoogleBigqueryLoader(BaseLoader, CSVToDBAPIMixin):
    def __init__(
            self,
            table: str,
            filename: str,
            google_bigquery_connector: 'GoogleBigqueryConnector' = None,
            dataset: str = None,
            create_table_ddl: str = None,
            mode: str = const.LOAD_OVERWRITE,
            primary_keys: Union[str, List[str]] = None,
            columns: Union[str, List[str]] = None,
            skiprows: int = 0,
            delete_file: bool = True,
            pre_queries: str = None,
            post_queries: str = None,
            *args, **kwargs
    ):
        self.table = table
        self.dataset = dataset

        self.google_bigquery = google_bigquery_connector

        # determine table name of target table and staging table
        self.filename = filename  # full file path
        self.skiprows = skiprows

        # determine table ddl stuff
        self.create_table_ddl = create_table_ddl

        # merge stuff
        if mode not in allowed_modes:
            raise ValueError(f'mode should be one of ({allowed_modes})')

        self.mode = mode
        self.primary_keys = ensure_str_list(primary_keys)
        if self.mode == const.LOAD_MERGE and not self.primary_keys:
            raise ValueError('primary_keys should not be empty in mode {}'.format(const.LOAD_MERGE))

        self.columns = ensure_str_list(columns)

        self.pre_queries = ensure_query_list(pre_queries) or []
        self.post_queries = ensure_query_list(post_queries) or []

        self.delete_file = delete_file

        super().__init__()

    def execute_impl(self):
        if fs.is_file_empty(self.filename):
            self.logger.error('file not exists or has no content. %s', self.filename)
            fs.remove_files_safely(fs.schema_filename(self.filename))
            return

        self._prepare_target_table()
        self._prepare_staging_table()
        self._merge_into_target_table()

        # do cleaning things
        if self.delete_file:
            self.logger.info('delete local file %s', self.filename)
            fs.remove_files_safely(self.filename)
            fs.remove_files_safely(fs.schema_filename(self.filename))

    @property
    def connector(self):
        return self.google_bigquery

    @property
    def staging_table(self):
        return staging_table_of(self.table)

    @property
    def full_staging_table_name(self):
        return f'{self.dataset}.{self.staging_table}'

    @property
    def full_table_name(self):
        return f'{self.dataset}.{self.table}'

    def _prepare_target_table(self):
        # add schema for azure data warehouse, dataset for google bigquery
        if self.connector.has_table(table=self.table, schema=getattr(self, 'schema', None),
                                    dataset=getattr(self, 'dataset', None)):
            return

        self.logger.info('table not found, try to create it')
        ddl = self._infer_create_table_ddl()
        if not ddl:
            raise ValueError('table not found, create_table_ddl is required')
        ddl = ddl.strip().rstrip(';')
        self.logger.info('create table ddl: %s\n', ddl)
        with self.connector.cursor() as cursor:
            cursor.execute(ddl)

    def _prepare_staging_table(self):
        dataset, table = self.full_staging_table_name.split('.')
        drop = f'DROP TABLE IF EXISTS {self.full_staging_table_name}'
        staging_ddl = f'CREATE TABLE IF NOT EXISTS {self.full_staging_table_name} LIKE {self.full_table_name}'
        self.connector.execute([drop, staging_ddl], auto_commit=False, commit_on_close=True)

        self.logger.info(f'load {self.filename} into staging table {self.full_staging_table_name}')
        self.connector.load_csv(table=self.full_staging_table_name,
                                filename=self.filename,
                                schema=self.connector.get_schema(table, dataset),
                                skiprows=self.skiprows)

    def _merge_into_target_table(self):
        target = self.full_table_name
        staging = self.full_staging_table_name

        append_sql = f'INSERT INTO {target} SELECT * FROM {staging}'
        if self.mode == const.LOAD_OVERWRITE:
            queries = [f'TRUNCATE TABLE {target}', append_sql]
        elif self.mode == const.LOAD_MERGE:
            queries = self._ingest_by_merging()
        else:
            # APPEND
            queries = [append_sql]

        queries.append(f'DROP TABLE {staging}')

        queries = self.pre_queries + queries + self.post_queries
        self.logger.info('running Google Bigquery queries...')
        self.connector.execute(queries)
        self.logger.info('done.')

    def _ingest_by_merging(self):
        reconcile = reconcile_table_of(self.table)
        bak = bak_table_of(self.table)

        quote = self.connector.quote_identifier
        join = ' AND '.join([f'a.{quote(x)} = b.{quote(x)}' for x in self.primary_keys])

        queries = f"""
            DROP TABLE IF EXISTS {self.dataset}.{reconcile};
            CREATE TABLE IF NOT EXISTS {self.dataset}.{reconcile} LIKE {self.full_table_name};
            
            INSERT INTO {self.dataset}.{reconcile}
            SELECT a.*
            FROM {self.full_table_name} AS a
            LEFT JOIN {self.full_staging_table_name} AS b ON {join}
            WHERE b.{quote(self.primary_keys[0])} IS NULL
            UNION ALL
            SELECT * FROM {self.full_staging_table_name};

            ALTER TABLE {self.full_table_name} RENAME TO {bak};
            ALTER TABLE {self.dataset}.{reconcile} RENAME TO {self.table};

            DROP TABLE IF EXISTS {self.dataset}.{bak};
            DROP TABLE IF EXISTS {self.dataset}.{reconcile};
        """
        return queries.split(';')