import functools
import glob
import json
import os
import tempfile
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, Dict, List, Union

import cytoolz as toolz
from slugify import slugify

from recurvedata.pigeon import const
from recurvedata.pigeon.connector import new_hive_connector, new_impala_connector
from recurvedata.pigeon.csv import CSV
from recurvedata.pigeon.handler.csv_handler import convert_csv_to_hive_textfile
from recurvedata.pigeon.loader.base import BaseLoader, CSVToDBAPIMixin
from recurvedata.pigeon.utils import ensure_list, ensure_query_list, ensure_str_list, fs, silent
from recurvedata.pigeon.utils.sql import reconcile_table_of, staging_table_of

if TYPE_CHECKING:
    from recurvedata.pigeon.connector.hive_impala import HiveConnector, ImpalaConnector

allowed_modes = (
    const.LOAD_OVERWRITE,
    const.LOAD_MERGE,
    const.LOAD_APPEND
)

AUTO = object()


def _enable_connection_pooling(method):
    @functools.wraps(method)
    def inner(self: 'CSVToHiveLoader', *args, **kwargs):
        self.hive.enable_connection_pooling(reset_on_return=False)
        self.impala.enable_connection_pooling(reset_on_return=False)
        try:
            return method(self, *args, **kwargs)
        except BaseException as e:
            raise e
        finally:
            self.hive.dispose()
            self.impala.dispose()

    return inner


class CSVToHiveLoader(BaseLoader, CSVToDBAPIMixin):
    def __init__(
            self,
            database: str,
            table: str,
            filename: str,
            hive_connector: 'HiveConnector' = None,
            impala_connector: 'ImpalaConnector' = None,
            create_table_ddl: str = None,
            dynamic_partition: str = None,
            partition: Dict = None,
            mode: str = const.LOAD_OVERWRITE,
            primary_keys: List[str] = None,
            using_impala: bool = AUTO,
            delete_file: bool = False,
            dedup: bool = False,
            dedup_uniq_keys: List[str] = None,
            dedup_orderby: str = None,
            pre_queries: Union[str, List[str]] = None,
            post_queries: Union[str, List[str]] = None,
            is_std_csv: bool = False,
            has_header: bool = False,
            csv_options: Dict = None,
            compression_codec: str = "snappy",
            dumper_meta: Dict = None,
            refresh_impala_metadata: bool = True
    ):
        """Loads csv file into a Hive table.

        :param database: the target database name
        :param table: target table name, should not contains database portion
        :param filename: the absolute path to csv file, can be a single string or list of strings
        :param hive_connector: a HiveConnector object used to query Hive
        :param impala_connector: a ImpalaConnector object used to query Impala
        :param create_table_ddl: create table
        :param dynamic_partition: dynamic_partition specs,should be a string like 'site,month'
        :param partition: partition specs, should be a dict like {'dt': '2017-01-01'}
        :param mode: one of (LOAD_OVERWRITE, LOAD_MERGE, LOAD_APPEND)
        :param primary_keys: columns that identifies a unique row, e.g. ['dt', 'product_id']. Required if mode is LOAD_MERGE
        :param using_impala: whether use Impala to merge data or not. Possible values:
                             - `AUTO` (by default): determine by whether the table has complex type fields.
                             - `True`: use Impala, will fail if the table has complex type fields
                             - `False` and other values: fallback to use Hive
        :param delete_file: delete the CSV file after loading, default is True
        :param dedup: remove duplicated records from staging table before being merged into target
        :param dedup_uniq_keys: columns that identifies a unique row.
        :param dedup_orderby: determine which row should be kept.
                              e.g. "to keep the row has minimal timestamp", then set `dedup_orderby='timestamp ASC'
        :param pre_queries: queries executed before loading
        :param post_queries: queries after loading
        :param is_std_csv: indicates the input filename is a standard CSV file or not (standard Hive TextFile)
        :param compression_codec: compression format code,emum{none,snappy,gzip}
        :param dumper_meta: dumper output and options like check_dumper_row
        """
        self.database = database
        self.table = table

        if hive_connector is None:
            hive_connector = new_hive_connector(database=self.database)
        else:
            hive_connector.database = self.database
        self.hive = hive_connector

        if impala_connector is None:
            impala_connector = new_impala_connector(database=self.database)
        else:
            impala_connector.database = self.database
        self.impala = impala_connector
        self.refresh_impala_metadata = refresh_impala_metadata

        self.filename = filename
        self._local_data_files = self._determine_local_data_files()
        self._schema_filename = self._infer_schema_filename()

        self.is_std_csv = is_std_csv
        self.has_header = has_header
        self.csv_options = csv_options or {}

        self.create_table_ddl = create_table_ddl
        # 原来的partition重新命名为static_partiton，构造函数传入变量不换，避免修改大量的业务代码
        self.static_partition = partition
        if dynamic_partition:
            self.dynamic_partition = dynamic_partition.split(',')
        else:
            self.dynamic_partition = None
        if self.static_partition and self.dynamic_partition:
            raise ValueError('Partition mode only be static or dynamic')
        if self.dynamic_partition and not self.connector.is_table_partitioned(self.database, self.table):
            if not create_table_ddl or 'partitioned by' not in self.create_table_ddl.lower():
                raise ValueError("Table not found or is not partitioned, create_table_ddl is required and "
                                 "assign partition columns when use dynamic partition mode")

        if mode not in allowed_modes:
            raise ValueError('mode should be one of ({})'.format(allowed_modes))

        self.mode = mode
        self.primary_keys = ensure_str_list(primary_keys)
        if self.mode == const.LOAD_MERGE and not self.primary_keys:
            raise ValueError('primary_keys should not be empty in mode {}'.format(const.LOAD_MERGE))
        if self.mode == const.LOAD_MERGE and (self.static_partition or self.dynamic_partition):
            raise ValueError('merge into partitioned table is not supported')

        self.delete_file = delete_file
        self.using_impala = using_impala

        self.dedup = dedup
        self.dedup_uniq_keys = ensure_str_list(dedup_uniq_keys)
        self.dedup_orderby = dedup_orderby
        if self.dedup and not self.dedup_uniq_keys:
            raise ValueError('dedup_uniq_keys should not be empty')
        if not self.dedup_orderby:
            self.dedup_orderby = ', '.join(self.dedup_uniq_keys)

        self.pre_queries = ensure_query_list(pre_queries) or []
        self.post_queries = ensure_query_list(post_queries) or []
        self.compression_codec = compression_codec
        self.dumper_meta = dumper_meta

        super().__init__()

    @property
    def schema_filename(self) -> str:
        return self._schema_filename

    @_enable_connection_pooling
    def execute_impl(self):
        if all([fs.is_file_empty(x) for x in self._local_data_files]):
            self.logger.error('file not exists or has no content. %s', self.filename)
            self._cleanup()
            return

        self._prepare_target_table()
        self._check_target_table_cols_num()
        self._prepare_staging_table()
        self._merge_into_target_table()
        if self.refresh_impala_metadata:
            self._compute_stats()

        if self.delete_file:
            self._cleanup()

    @property
    def slugify_partition(self) -> str:
        if self.static_partition is None:
            return ''
        names = [slugify(str(value), separator='') for _, value in self.static_partition.items()]
        return '_'.join(names)

    @property
    def staging_table(self) -> str:
        if not self.static_partition:
            table_name = staging_table_of(self.table)
        else:
            table_name = staging_table_of(f'{self.table}_{self.slugify_partition}')
        return table_name[:120]

    @property
    def reconciled_table(self) -> str:
        if not self.static_partition:
            table_name = reconcile_table_of(self.table)
        else:
            table_name = reconcile_table_of(f'{self.table}_{self.slugify_partition}')
        return table_name[:120]

    @property
    def connector(self) -> 'HiveConnector':
        return self.hive

    def _determine_local_data_files(self) -> List[str]:
        if isinstance(self.filename, str) and os.path.isdir(self.filename):
            raise TypeError('filename should neither be a single path or list of paths, directory is not supported')

        # ignore the empty or non-exist files
        files = [x for x in ensure_list(self.filename) if not x.endswith('.schema') and not fs.is_file_empty(x)]

        # make sure the first file is not empty
        files.sort(key=lambda x: os.path.getsize(x), reverse=True)
        return files

    def _infer_schema_filename(self) -> str:
        if self._local_data_files:
            f = self._local_data_files[0]
        elif self.filename:
            f = ensure_list(self.filename)[0]
        else:
            return None
        return fs.schema_filename(os.path.splitext(f)[0])

    def _cleanup(self):
        fs.remove_files_safely(self.filename)
        fs.remove_files_safely(self._schema_filename)

    def _check_target_table_cols_num(self):
        # 获取目标表的字段长度信息
        if not self.static_partition:
            exclude = None
        else:
            exclude = self.static_partition.keys()
        target_table_cols = self.connector.get_columns(table=self.table, database=self.database, exclude=exclude)

        # 解析schema文件，获取fields长度信息
        if not fs.is_file_empty(self._schema_filename):
            with open(self._schema_filename) as f:
                try:
                    schema_fields = json.load(f)
                    if len(schema_fields) == len(target_table_cols):
                        return
                except JSONDecodeError:
                    pass

        # 解析csv数据文件，获取列的数量
        if self.is_std_csv:
            cf = CSV(self._local_data_files[0], **self.csv_options)
            with cf.reader(as_dict=False) as reader:
                row = next(reader)
            schema_fields_num = len(row)
        else:
            # hive格式的csv
            with open(self._local_data_files[0]) as f:
                line = next(f)
            schema_fields_num = len(line.split(const.HIVE_FIELD_DELIMITER))
        if schema_fields_num != len(target_table_cols):
            raise Exception(f'number of columns mismatch, target table has {target_table_cols} columns,'
                            f' while data file has {schema_fields_num}')

    def _prepare_staging_table(self):
        staging_table = self.hive.quote_identifier(self.staging_table)
        queries = [
            f"DROP TABLE IF EXISTS {staging_table} PURGE;"
        ]
        exclude_columns = self.static_partition.keys() if self.static_partition else None
        staging_ddl = self.hive.generate_load_staging_table_ddl(staging_table, self.table, self.database,
                                                                exclude_columns=exclude_columns)
        queries.append(staging_ddl)
        self.hive.execute(queries)

        path_to_load = self._local_data_files
        if self.is_std_csv:
            self.logger.info('got standard CSV file, convert to Hive text file before loading')
            prefix = os.path.splitext(os.path.basename(self._local_data_files[0]))[0]
            tmp_folder = tempfile.mkdtemp(prefix=f'{prefix}_', dir=os.path.dirname(self._local_data_files[0]))
            if os.path.exists(tmp_folder):
                self.logger.warning(f'tmp folder {tmp_folder} already exists, will overwrite any files if exist')
                fs.remove_folder_safely(tmp_folder)
            os.makedirs(tmp_folder, exist_ok=True)

            for cf in self._local_data_files:
                convert_csv_to_hive_textfile(cf, folder=tmp_folder, replace=False,
                                             has_header=self.has_header, **self.csv_options)
            path_to_load = glob.glob(os.path.join(tmp_folder, '*'))
            self.logger.info(f'the real files to be loaded into {self.staging_table} are {path_to_load}')

        self.hive.load_local_file(self.staging_table, path_to_load)

        if self._determine_using_impala():
            self.impala.execute(f'INVALIDATE METADATA {self.impala.quote_identifier(self.staging_table)}')

        self._check_staging_table_rows()

        # remove the temp files
        if path_to_load != self._local_data_files:
            self.logger.info(f'delete {path_to_load} after being loaded to {self.staging_table}')
            fs.remove_folder_safely(os.path.dirname(path_to_load[0]))

    def _construct_dedup_query(self) -> str:
        partition_cols = []
        for col in self.dedup_uniq_keys:
            partition_cols.append(self.hive.quote_identifier(col))
        partition_by = ', '.join(partition_cols)

        cols = self.hive.get_columns(self.staging_table)
        staging_table = self.hive.quote_identifier(self.staging_table)

        query = f'''
            WITH t AS (
              SELECT *, ROW_NUMBER() OVER(PARTITION BY {partition_by} ORDER BY {self.dedup_orderby}) AS rnk
              FROM {staging_table}
            )
            INSERT OVERWRITE TABLE {staging_table}
            SELECT {', '.join(self.hive.quote_identifier(x) for x in cols)}
            FROM t WHERE rnk = 1
        '''
        return query

    def _get_compression_sqls(self) -> List[str]:
        using_impala = self._determine_using_impala()
        compression_sqls = []
        if using_impala:
            allow_text = "SET ALLOW_UNSUPPORTED_FORMATS=True"
            set_codec = "SET COMPRESSION_CODEC = {}".format(self.compression_codec)
            compression_sqls = [allow_text, set_codec]
        else:
            if self.compression_codec != "none" and self._is_low_hive_version():
                set_codec = "SET parquet.compression = {}".format(self.compression_codec)
                compression_sqls = [set_codec]
        return compression_sqls

    def _merge_into_target_table(self):
        if self.dedup:
            self.pre_queries.append(self._construct_dedup_query())

        if self.mode in (const.LOAD_OVERWRITE, const.LOAD_APPEND):
            queries = self._ingest_by_overwriting_appending()
        else:
            queries = self._ingest_by_merging()

        queries.append('DROP TABLE IF EXISTS {} PURGE'.format(self.hive.quote_identifier(self.staging_table)))
        all_queries = self.pre_queries + queries + self.post_queries
        self._execute_merge_queries(all_queries)

    def _ingest_by_overwriting_appending(self) -> List[str]:
        compression_sqls = self._get_compression_sqls()
        insert_mode = {
            const.LOAD_OVERWRITE: 'OVERWRITE',
            const.LOAD_APPEND: 'INTO'
        }
        partition = ''
        if self.static_partition:
            spec = ', '.join([f'{self.hive.quote_identifier(k)}={repr(v)}' for k, v in self.static_partition.items()])
            partition = f'PARTITION ({spec})'
        elif self.dynamic_partition:
            spec = ', '.join(self.hive.quote_identifier(p) for p in self.dynamic_partition)
            partition = f'PARTITION ({spec})'

        queries = []
        if not self._determine_using_impala():
            queries.append('SET hive.exec.dynamic.partition.mode=nonstrict')
        sql = 'INSERT {mode} TABLE {table} {partition} SELECT * FROM {staging}'.format(
            mode=insert_mode[self.mode], partition=partition,
            table=self.hive.quote_identifier(self.table),
            staging=self.hive.quote_identifier(self.staging_table))
        queries.append(sql)
        return compression_sqls + queries

    def _ingest_by_merging(self) -> List[str]:
        reconcile = self.reconciled_table
        join = ' AND '.join(
            [f'a.{self.hive.quote_identifier(x)} = b.{self.hive.quote_identifier(x)}' for x in self.primary_keys])
        sql = '''
            DROP TABLE IF EXISTS {reconcile} PURGE;
            CREATE TABLE {reconcile} STORED AS PARQUET AS
            SELECT a.* FROM {table} a LEFT OUTER JOIN {staging} b ON {join} WHERE b.{pk} IS NULL
            UNION ALL
            SELECT * FROM {staging};
            {compression_sqls};
            INSERT OVERWRITE TABLE {table} SELECT * FROM {reconcile};
            DROP TABLE IF EXISTS {reconcile} PURGE;
        '''.format(reconcile=self.hive.quote_identifier(reconcile),
                   table=self.hive.quote_identifier(self.table),
                   staging=self.hive.quote_identifier(self.staging_table),
                   compression_sqls=";".join(self._get_compression_sqls()),
                   # bak=self.hive.quote_identifier('{}_bak'.format(self.table)),
                   join=join,
                   pk=f'{self.hive.quote_identifier(self.primary_keys[0])}')
        queries = sql.split(';')
        return queries

    def _execute_merge_queries(self, queries: List[str]):
        using_impala = self._determine_using_impala()
        if using_impala:
            # staging_update_meta = f'INVALIDATE METADATA {self.impala.quote_identifier(self.staging_table)}'
            # self.impala.execute(staging_update_meta)
            self.impala.refresh(self.table, compute_stats=False)
            self.impala.execute(queries)
        else:
            if self.dynamic_partition:
                allow_dynamic_partition_queries_list = ['SET hive.exec.dynamic.partition=true',
                                                        'SET hive.exec.dynamic.partition.mode=nonstrict']
                queries = allow_dynamic_partition_queries_list + queries

            self.hive.execute(queries)

    @toolz.memoize
    def _is_low_hive_version(self):
        """
        2.3.0 以下的版本, 动态修改 parquet 只能通过 SET parquet.compression = "xx" 的方式操作;
        2.3.0 以上的版本, 则只能在 create table 时指定
        """
        result = self.hive.fetchall('SELECT version()')
        self.logger.info(f"current hive's version: {result[0][0]}")
        return result[0][0] < "2.3.0"

    @toolz.memoize
    def _determine_using_impala(self) -> bool:
        if self.impala is None:
            self.logger.info('impala connector is not set')
            return False

        if self.using_impala is True:
            self.logger.info('`using_impala` is set to True by caller')
            return True

        if self.using_impala is AUTO:
            self.logger.info('`using_impala` is set to AUTO, checking complex type fields')
            if not self.hive.has_complex_type_fields(self.table):
                self.logger.info('found no complex type fields, happy to use Impala')
                return True
            self.logger.info('detected complex type fields, fallback to using Hive')
        return False

    @silent()
    def _compute_stats(self):
        self.impala.refresh(self.table, True)

    def _check_staging_table_rows(self):
        if not self.dumper_meta:
            return
        check_dumper_row: bool = self.dumper_meta.get('check_dumper_row', True)
        dumper_rows: int = self.dumper_meta.get('dumper_output_rows')
        if not (check_dumper_row and dumper_rows):
            return
        staging_table = self.impala.quote_identifier(self.staging_table)
        if self._determine_using_impala():
            # self.impala.execute(f'INVALIDATE METADATA {staging_table}')
            staging_table_cnt, = self.impala.fetchone(f'SELECT COUNT(1) AS cnt FROM {staging_table}')
        else:
            staging_table_cnt, = self.hive.fetchone(f'SELECT COUNT(1) AS cnt FROM {staging_table}')
        if staging_table_cnt != dumper_rows:
            raise ValueError(f'staging table {staging_table} cnt {staging_table_cnt} != dumper_rows {dumper_rows} '
                             'maybe something wrong when load csv to staging table, please retry')
        self.logger.info(f'staging_table {staging_table} cnt {staging_table_cnt} equals with dumper_output')
