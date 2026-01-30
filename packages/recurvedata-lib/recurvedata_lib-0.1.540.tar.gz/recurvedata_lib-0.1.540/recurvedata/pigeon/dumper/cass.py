import multiprocessing

from cassandra.query import FETCH_SIZE_UNSET, SimpleStatement, tuple_factory

from recurvedata.pigeon.connector.cass import CassandraConnector
from recurvedata.pigeon.dumper.base import BaseDumper, SQLBasedWorker
from recurvedata.pigeon.utils import ensure_list, ensure_str_list, mp
from recurvedata.pigeon.utils import sql as sqlutils


class CassandraDumperWorker(SQLBasedWorker):
    def dump_query(self, query, parameters=None):
        # if isinstance(query, str):
        #     query = sqlutils.sqlformat(query)
        self.logger.info("running query `%s` with parameters: %s", query, parameters)

        with self.connector.closing_session() as session:
            session.row_factory = tuple_factory

            # Cassandra 2.0+ offers support for automatic query paging.
            result_set = session.execute(query, parameters, timeout=30)
            schema = self.connector.get_data_schema(result_set)
            self.set_input_schema(schema)
            col_names = result_set.column_names
            # col_types = result_set.column_types
            for row in result_set:
                yield self.row_factory(col_names, row)


class CassandraDumper(BaseDumper):
    def __init__(
        self,
        connector,
        table,
        columns=None,
        where=None,
        partition_column=None,
        partitions=None,
        splits=1,
        concurrency=1,
        page_size=FETCH_SIZE_UNSET,
        consistency_level=None,
        retries=3,
        handler_factories=None,
    ):
        """The base class that dumps rows from Cassandra.

        :param connector: the connector object
        :type connector: pigeon.database.CassandraConnector
        :param table: the table name
        :type table: str
        :param columns: columns to query
        :type columns: list | str
        :param where: where clause
        :type where: str
        :param partition_column: the partition column name
        :type partition_column: str
        :param partitions: specific partitions
        :type partitions: list
        :param concurrency: number of workers to dump data from partitions.
                       This is used only if `partitions` is not None, and
                       would be adjust to min(len(partitions), concurrency).
        :type concurrency: int
        :param splits: Deprecated, use `concurrency` instead
        :param retries: max retry number
        :param handler_factories: handler factories to create handlers
        :type handler_factories: list
        """
        super().__init__(handler_factories=handler_factories)

        self.concurrency = concurrency or splits or 1

        assert isinstance(connector, CassandraConnector)
        self.connector = connector

        self.table = table
        self.columns = ensure_str_list(columns)
        self.where = where

        if partitions is not None and partition_column is None:
            raise ValueError("partition_column must not be None")

        self.partitions = ensure_str_list(partitions)
        self.partition_column = partition_column
        if self.partitions:
            self.concurrency = min(len(self.partitions), self.concurrency)
        self.retries = retries

        self.page_size = page_size
        self.consistency_level = consistency_level

        self._base_query = self.construct_query()
        self.worker_cls = CassandraDumperWorker

        self.meta.context = {
            "table": self.table,
            "columns": self.columns,
            "base_query": self.base_query,
            "where": self.where,
            "partition_column": self.partition_column,
            "partitions": self.partitions,
            "concurrency": self.concurrency,
        }

    @property
    def base_query(self):
        return self._base_query

    def construct_query(self):
        project = "*"
        if self.columns:
            project = ", ".join(self.columns)
        query = "SELECT {} FROM {}".format(project, self.table)

        if self.partitions:
            query += " WHERE {} = %s".format(self.partition_column)

        query = sqlutils.apply_where_safely(query, self.where)
        return query.strip(";")

    def execute(self):
        self.meta.mark_start()
        if self.concurrency <= 1:
            rv = self.execute_in_serial()
        else:
            rv = self.execute_in_parallel()
        self.meta.mark_finish()
        self.collect_meta(rv)
        self.logger.info("dump meta: %s", self.meta.to_json(indent=2))
        self.handle_schema()
        return self.meta

    def _create_worker(self, **kwargs):
        query = SimpleStatement(self.base_query, fetch_size=self.page_size, consistency_level=self.consistency_level)
        options = {
            "row_factory": self.row_factory,
            "query": query,
            "connector": self.connector,
            "retries": self.retries,
        }
        options.update(kwargs)
        return self.worker_cls(**options)

    def execute_in_serial(self):
        workers_meta = []
        if self.partitions:
            for idx, partition in enumerate(self.partitions):
                handlers = self.create_handlers()
                worker = self._create_worker(worker_id=1, task_id=idx, parameters=(partition,), handlers=handlers)
                workers_meta.append(worker.execute())
        else:
            handlers = self.create_handlers()
            worker = self._create_worker(worker_id=1, task_id=1, parameters=None, handlers=handlers)
            workers_meta.append(worker.execute())
        self.join_handlers()
        return workers_meta

    def execute_in_parallel(self):
        if not self.partitions:
            self.logger.info("there are no partitions, fallback to single process")
            return self.execute_in_serial()

        workers = []
        result_queue = multiprocessing.Queue()
        task_queue = multiprocessing.Queue()
        for idx in range(self.concurrency):
            p = multiprocessing.Process(target=self.run_worker, args=(idx, task_queue, result_queue))
            p.start()
            workers.append(p)

        for idx, p in enumerate(self.partitions):
            self.logger.info("sending partition %d %s to task queue", idx, p)
            handlers = self.create_handlers()
            task_queue.put((idx, p, handlers))

        self.logger.info("sending finish signal to workers")
        for _ in workers:
            task_queue.put(None)

        self.logger.info("waiting for workers to finish")
        workers_meta = mp.safe_join_subprocesses(workers, result_queue)
        self.join_handlers()

        # some works failed
        num_total_tasks = len(self.partitions)
        num_success_tasks = len(workers_meta)
        if num_success_tasks < num_total_tasks:
            raise RuntimeError(f"only {num_success_tasks} of {num_total_tasks} tasks succeeded")

        return workers_meta

    def run_worker(self, worker_id, task_queue, result_queue):
        while True:
            task = task_queue.get()
            if task is None:
                self.logger.info("got None partition, exist.")
                break
            task_id, partition, handlers = task
            worker = self._create_worker(
                worker_id=worker_id, task_id=task_id, parameters=(partition,), handlers=handlers
            )
            n = worker.execute()
            result_queue.put(n)

    def collect_meta(self, workers_meta):
        workers_meta = ensure_list(workers_meta)
        for meta in workers_meta:
            self.meta.num_dumped_rows += meta.num_dumped_rows
            for i, hf in enumerate(self.handler_factories):
                hf.meta.update(meta.handlers_meta[i])

        self.meta.schema = workers_meta[0].schema
        self.meta.handlers_meta = [x.meta for x in self.handler_factories]
