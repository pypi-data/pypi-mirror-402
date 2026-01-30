import datetime
import multiprocessing
import os
from typing import TYPE_CHECKING, Dict, List, Tuple, TypeVar, Union

from recurvedata.pigeon.connector.dbapi import DBAPIConnector
from recurvedata.pigeon.const import CLICKHOUSE_MAX_ROW_BUFFER
from recurvedata.pigeon.dumper.base import BaseDumper, SQLBasedWorker
from recurvedata.pigeon.utils import ensure_list, mp
from recurvedata.pigeon.utils import sql as sqlutils

if TYPE_CHECKING:
    from recurvedata.pigeon.handler import HandlerFactory
    from recurvedata.pigeon.meta import DumperMeta, DumperWorkerMeta

DONE = 'TASK_DONE'

T = TypeVar('T')


class DBAPIDumperWorker(SQLBasedWorker):
    def dump_query(self, sql: str, parameters: Union[List, Tuple, Dict] = None):
        # sql = sqlutils.sqlformat(sql)
        self.logger.info('running query:\n%s\nwith parameters: %s', sql, parameters)

        cursor_options = {'commit_on_close': False}
        if self.connector.is_postgres() or self.connector.is_redshift():
            ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            cursor_options['cursor_name'] = f'pigeon_{self.worker_id}_{ts}'
        elif self.connector.is_clickhouse_native():
            cursor_options.update({
                'stream': True,
                'max_rows': CLICKHOUSE_MAX_ROW_BUFFER
            })

        with self.connector.cursor(**cursor_options) as cursor:
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)

            # Postgres 使用 server side cursor, 要先 fetch 数据才能获取到 cursor.description
            if self.connector.is_postgres() or self.connector.is_redshift():
                row = cursor.fetchone()
                schema = self.connector.cursor_to_schema(cursor)
                self.set_input_schema(schema)

                if row is None:
                    # 没有结果，直接返回，否则下面再 fetch 会抛出异常
                    # opening multiple cursors from within the same client connection is not allowed.
                    return
            else:
                row = None

            schema = self.connector.cursor_to_schema(cursor)
            self.set_input_schema(schema)
            col_names = schema.field_names

            if row:
                yield self.row_factory(col_names, row)

            for row in cursor:
                yield self.row_factory(col_names, row)


class DBAPIDumper(BaseDumper):
    def __init__(
            self,
            connector: DBAPIConnector,
            table: str = None,
            sql: str = None,
            splitby: str = None,
            splits: int = 1,
            concurrency: int = None,
            retries: int = 3,
            handler_factories: List['HandlerFactory'] = None
    ):
        """The base class that performs a dumping operation against a DBMS over DBAPI.

        :param connector: the connector object
        :param table: the table name, this is equivalent to pass sql as 'SELECT * FROM table'
        :param sql: the sql query to perform
        :param splitby: the column used to split tasks
        :param splits: 切分成 splits 个任务，每个任务失败后会单独重试
        :param concurrency: 并发数，同时 concurrency 个进程执行任务
        :param retries: 每个任务的重试次数
        :param handler_factories: handler factories to create handlers
        """
        super().__init__(handler_factories=handler_factories)

        self.splits = splits
        self.concurrency = splits if concurrency is None else concurrency
        self.retries = retries

        assert isinstance(connector, DBAPIConnector)
        self.connector = connector

        self.table = table
        self.sql = sql
        self._base_query = self.construct_query()
        self.splitby = splitby

        if not self.splitby:
            self.logger.warning('split column is not set, reset concurrency and splits')
            self.concurrency = 1
            self.splits = 1

        self.worker_cls = DBAPIDumperWorker

        self.meta.context = {
            'table': self.table,
            'sql': self.sql,
            'base_query': self.base_query,
            'splitby': self.splitby,
            'splits': self.splits,
            'concurrency': self.concurrency,
        }

    @property
    def base_query(self) -> str:
        return self._base_query

    def construct_query(self) -> str:
        if self.sql:
            query = self.sql
        elif self.table:
            query = f'SELECT * FROM {self.connector.quote_identifier(self.table)}'
        else:
            raise ValueError('either table or sql is required')

        # if self.connector.is_mysql():
        #     query = sqlutils.apply_sql_no_cache(query)
        return query.strip(';')

    def _create_worker(self, **kwargs) -> DBAPIDumperWorker:
        return self.worker_cls(
            **kwargs,
            row_factory=self.row_factory,
            connector=self.connector,
            retries=self.retries
        )

    def execute(self) -> 'DumperMeta':
        self.meta.mark_start()
        if self.splits <= 1:
            rv = self.execute_in_serial()
        else:
            rv = self.execute_in_parallel()
        self.meta.mark_finish()
        self.collect_meta(rv)
        self.logger.info('dumper meta: %s', self.meta.to_json(indent=2))
        self.handle_schema()
        return self.meta

    def execute_in_serial(self) -> List['DumperWorkerMeta']:
        handlers = self.create_handlers()
        worker = self._create_worker(worker_id=0, task_id=0, query=self.base_query,
                                     parameters=None, handlers=handlers)

        worker_meta = worker.execute()
        self.join_handlers()
        return [worker_meta]

    def execute_in_parallel(self) -> List['DumperWorkerMeta']:
        lower, upper = self._determine_boundary()
        self.logger.info('got boundary: (%s, %s)', lower, upper)
        if lower is None and upper is None:
            self.logger.info('bad boundary values, fallback to single process')
            return self.execute_in_serial()
        if lower == upper:
            self.logger.info('lower and upper boundary are the same, fallback to single process')
            return self.execute_in_serial()

        ranges = self._split_ranges(lower, upper, self.splits)

        split_col = self.connector.quote_identifier(self.splitby)
        tasks = []
        for idx, (start, end) in enumerate(ranges):
            include_upper = (idx == len(ranges) - 1)  # the last split should include the upper bound
            if self.connector.is_impala() or self.connector.is_clickhouse_native():
                # 截至 2018-05-30, impyla 使用 list、tuple 格式化参数的时候会有 bug
                # 详情见 https://github.com/cloudera/impyla/pull/156#issuecomment-159790585
                # 本来应该给 impyla 提交 issue 或 PR，但这个项目感觉像死了。。。先在上层规避
                markers = ['%(start)s', '%(end)s']
                params = {'start': start, 'end': end}
            elif self.connector.is_azure_synapse() or self.connector.is_mssql() or self.connector.is_phoenix():
                markers = ['?', '?']
                params = (start, end)
            else:
                markers = ['%s', '%s']
                params = (start, end)

            # phoenix 日期作为参数传入会报错，直接把 SQL 格式化好
            less_than = f'<{"=" if include_upper else ""}'
            if self.connector.is_phoenix() and isinstance(start, datetime.date):
                where = f"{split_col} >= TIMESTAMP '{params[0]}' AND {split_col} {less_than} TIMESTAMP '{params[1]}'"
                params = None
            else:
                where = f'{split_col} >= %s AND {split_col} {less_than} %s' % tuple(markers)
            query = sqlutils.apply_where_safely(self.base_query, where)
            handlers = self.create_handlers()
            tasks.append((idx, query, params, handlers))

        task_queue = multiprocessing.Queue()
        for task in tasks:
            task_queue.put(task)
        for i in range(self.concurrency):
            task_queue.put(DONE)

        workers = []
        result_queue = multiprocessing.Queue()
        for i in range(self.concurrency):
            p = multiprocessing.Process(target=self.run_worker, args=(i, task_queue, result_queue))
            workers.append(p)
            p.start()

        self.logger.info('waiting for workers to finish')
        workers_meta, is_early_stop = mp.safe_join_subprocesses_early_stop(workers, result_queue)
        if is_early_stop:
            self.logger.info(f'early stop because some task failed, terminate all workers')
            mp.terminate_processes(workers)
            raise RuntimeError(f'early stop because some task failed')
        # 从一个 worker 中提取 input_schema，并赋值到每个 handler_factory 下的 input_schema
        for wm in workers_meta:
            if wm.schema is not None:
                self.set_input_schema(wm.schema)

        self.join_handlers()

        # some works failed
        num_total_tasks = len(tasks)
        num_success_tasks = len(workers_meta)
        if num_success_tasks < num_total_tasks:
            raise RuntimeError(f'only {num_success_tasks} of {num_total_tasks} tasks succeeded')

        return workers_meta

    def run_worker(self, worker_id: int, task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
        pid = os.getpid()
        self.logger.info(f'Worker#{worker_id} pid={pid} started')
        while True:
            task = task_queue.get()
            if task == DONE:
                break
            task_id, query, parameters, handlers = task
            worker = self._create_worker(
                worker_id=worker_id,
                task_id=task_id,
                query=query,
                parameters=parameters,
                handlers=handlers)
            result = worker.execute()
            result_queue.put(result)
        self.logger.info(f'Worker#{worker_id} pid={pid} exited')

    def collect_meta(self, workers_meta: Union['DumperWorkerMeta', List['DumperWorkerMeta']]):
        workers_meta = ensure_list(workers_meta)
        for meta in workers_meta:
            self.meta.num_dumped_rows += meta.num_dumped_rows
            for hf, hm in zip(self.handler_factories, meta.handlers_meta):
                hf.meta.update(hm)

        self.meta.schema = [x.schema for x in workers_meta if x.schema is not None][0]
        self.meta.handlers_meta = [x.meta for x in self.handler_factories]

    def _determine_boundary(self) -> Tuple[T, T]:
        lower = self._select_min_max(self.splitby, max_=False)
        upper = self._select_min_max(self.splitby, max_=True)
        return lower, upper

    def _select_min_max(self, col: str, max_: bool=False) -> T:
        from_clause = sqlutils.extract_from_clause(self.base_query)
        where_clause = sqlutils.extract_where_clause(self.base_query)
        ctx = {
            'col': self.connector.quote_identifier(col),
            'f': f'{from_clause}\n',
            'w': where_clause and f'{where_clause}\n' or '',
            'direction': 'DESC' if max_ else 'ASC'
        }
        if self.connector.is_azure_synapse() or self.connector.is_mssql():
            sql = 'SELECT TOP 1 {col} FROM {f} {w} ORDER BY {col} {direction}'.format(**ctx)
        else:
            sql = 'SELECT {col} FROM {f} {w} ORDER BY {col} {direction} LIMIT 1'.format(**ctx)
        row = self.connector.fetchall(sql)
        if row:
            return row[0][0]
        return None

    @staticmethod
    def _split_ranges(start: T, end: T, splits: int) -> List[Tuple[T, T]]:
        assert end > start, 'end "{}" must be greater than start "{}"'.format(end, start)

        convert_str = False
        if isinstance(start, str):
            convert_str = True
            # treat as date/datetime，only support `%Y-%m-%d` and `%Y-%m-%d %H:%M%S'
            if len(start) == len('2018-04-18'):
                # date
                start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
                end = datetime.datetime.strptime(end, '%Y-%m-%d').date()
            elif len(start) == len('2023-01-01 00:00:00.000000'):
                # datetime
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S.%f')
            else:
                # datetime
                start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

        if isinstance(start, datetime.datetime):
            size, remain = divmod((end - start).total_seconds(), splits)

            def delta(x):
                return datetime.timedelta(seconds=x)
        elif isinstance(start, datetime.date):
            # adjust number of splits according to the number of days
            days = (end - start).days
            splits = min(days, splits)
            size, remain = divmod(days, splits)

            def delta(x):
                return datetime.timedelta(days=x)
        else:
            size, remain = divmod(end - start, splits)

            def delta(x):
                return x

        ranges = []
        if size == 0:
            return [(start, end)]

        range_start = start
        for i in range(splits):
            range_end = range_start + delta(size)
            if remain > 0:
                range_end += delta(1)
                remain -= 1
            if i == splits - 1:
                range_end = end
            if convert_str:
                ranges.append((str(range_start), str(range_end)))
            else:
                ranges.append((range_start, range_end))
            range_start = range_end
        return ranges
