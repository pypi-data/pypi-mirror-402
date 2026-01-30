import csv
import itertools
import pickle
import re
import threading
from queue import Full, Queue

import sqlalchemy
import sqlalchemy.engine.url
import sqlparse
from sqlalchemy.pool import QueuePool

from recurvedata.pigeon.schema import Schema
from recurvedata.pigeon.utils import LoggingMixin, replace_null_values, trim_prefix, trim_suffix
from recurvedata.pigeon.utils.timing import TimeCounter


class NullCursor(LoggingMixin):
    """
    NullCursor implements DBAPI Cursor but does nothing at all.
    """

    def execute(self, operation, args=None, **kwargs):
        if args is None:
            sql = operation
        else:
            sql = operation % args
        self.logger.info(sql)
        return 0

    def executemany(self, query, args):
        if not args:
            return
        return sum(self.execute(query, arg) for arg in args)

    def fetchone(self):
        return None

    def fetchmany(self, size=None):
        return None

    def fetchall(self):
        return []

    def __iter__(self):
        return iter(self.fetchone, None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.logger.info("closing null cursor")


class _ShowTableLikeMixin(object):
    def has_table(self, table, database=None, cursor=None, **kwargs):
        close_cursor_at_exit = False
        if cursor is None:
            cursor = self.cursor()
            close_cursor_at_exit = True

        if database is not None and database != self.database:
            cursor.execute("USE {}".format(database))
        cursor.execute("SHOW TABLES LIKE '{}'".format(table))
        rv = cursor.fetchall()
        if close_cursor_at_exit:
            cursor.close()
        return bool(rv)


class _ConnectionPoolMixin(object):
    def enable_connection_pooling(self, **pool_kwargs):
        self.pooling_enabled = True
        self._pool_kwargs = pool_kwargs
        self._pools = {}  # we do not use lock, threadsafe is not guaranteed

    def get_connection_pooling_first(self, autocommit=False, *args, **kwargs):
        if not getattr(self, "pooling_enabled", False):
            return self.connect_impl(autocommit=autocommit, *args, **kwargs)

        pool_id = hash(pickle.dumps((autocommit, args, kwargs)))
        pool = self._pools.get(pool_id)
        if not pool:

            def creator():
                return self.connect_impl(autocommit=autocommit, *args, **kwargs)

            pool = QueuePool(creator=creator, **self._pool_kwargs)
            self._pools[pool_id] = pool
        conn = pool.connect()
        return conn

    def dispose(self):
        try:
            for _, p in self._pools.items():
                if isinstance(p, QueuePool):
                    p.dispose()
        except Exception as e:
            self.logger.error(f"dispose error: {e}")


class ClosingCursor:
    def __init__(self, connection, commit_on_close=True):
        self.connection = connection
        self._cursor = connection.cursor()
        self._commit_on_close = commit_on_close

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __enter__(self):
        return self

    def __iter__(self):
        # the Iterable check will not invoke __getattr__
        # we must delegates it explictly
        return iter(self._cursor)

    def __exit__(self, exc_type, exc, traceback):
        if not exc and self._commit_on_close:
            self.connection.commit()
        self.close()

    def close(self):
        self._cursor.close()
        self.connection.close()


class DBAPIConnector(LoggingMixin, _ConnectionPoolMixin):
    _log_query = True
    _sqla_driver = None
    _sqla_url_query = {}
    _identifier_start_quote = "`"
    _identifier_end_quote = "`"
    _param_placeholder = "%s"
    _default_port = None
    _default_database = None

    def __init__(self, host, port=None, database=None, user=None, password=None, schema=None, *args, **kwargs):
        self.host = host
        self.port = port or self._default_port
        self.database = database or self._default_database
        self.user = user
        self.password = password
        self.args = args
        self.kwargs = kwargs
        self.schema = schema

    def connect(self, autocommit=False, *args, **kwargs):
        """Returns a DBAPI connection"""
        return self.get_connection_pooling_first(autocommit, *args, **kwargs)

    def connect_impl(self, autocommit=False, *args, **kwargs):
        raise NotImplementedError("connect must be implemented by subclasses")

    def cursor(self, autocommit=False, dryrun=False, commit_on_close=True, **kwargs):
        """Returns a DBAPI cursor"""
        if dryrun:
            return NullCursor()
        conn = self.connect(autocommit, **kwargs)
        return ClosingCursor(conn, commit_on_close=commit_on_close)

    closing_cursor = cursor

    def execute(self, query, parameters=None, **cursor_options):
        """Execute one or more sql queries in a same session."""
        if isinstance(query, list):
            queries = list(itertools.chain(*map(sqlparse.split, query)))
        else:
            queries = sqlparse.split(query)

        with self.cursor(**cursor_options) as cursor:
            for q in queries:
                # remove the trailing `;`
                q = q.rstrip(";")
                if not q:
                    continue
                self._log(q)
                if parameters is not None:
                    cursor.execute(q, parameters)
                else:
                    cursor.execute(q)

    def fetchone(self, query, parameters=None):
        return self._fetch_query("one", query, parameters)

    def fetchmany(self, query, parameters=None, size=None):
        return self._fetch_query("many", query, parameters, size=size)

    def fetchall(self, query, parameters=None):
        return self._fetch_query("all", query, parameters)

    def _fetch_query(self, howmany, query, parameters=None, size=None):
        self._log(query)
        with self.cursor() as cursor:
            if parameters is not None:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            if howmany == "many":
                rv = cursor.fetchmany(size=size)
            elif howmany == "all":
                rv = cursor.fetchall()
            else:
                rv = cursor.fetchone()
        return rv

    def _log(self, msg, *args, **kwargs):
        if not self._log_query:
            return
        self.logger.info("\n" + str(msg), *args, **kwargs)

    def _get_sqlalchemy_uri(self):
        url = sqlalchemy.engine.url.URL(
            drivername=self._sqla_driver,
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=self.database,
            query=self._sqla_url_query,
        )
        return url.__to_string__(hide_password=False)

    def create_engine(self, engine_kwargs=None):
        """Returns a SQLAlchemy engine"""
        if engine_kwargs is None:
            engine_kwargs = {}
        # engine_kwargs.update({'encoding': 'utf8'})
        return sqlalchemy.create_engine(self._get_sqlalchemy_uri(), **engine_kwargs)

    def get_pandas_df(self, query, parameters=None, **kwargs):
        import pandas as pd

        query = sqlalchemy.text(query)  # if '%' in query, it will error without sqlalchemy.text in sqlalchemy 2.0
        con = self.create_engine()
        try:
            df = pd.read_sql_query(sql=query, con=con, params=parameters, **kwargs)
        finally:
            con.dispose()
        return df

    def has_table(self, table, database=None, **kwargs):
        raise NotImplementedError

    def clone(self):
        return self.__class__(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            schema=self.schema,
            *self.args,
            **self.kwargs,
        )

    def get_columns(self, table, database=None, exclude=None):
        if database is None:
            database = self.database
        with self.cursor() as cursor:
            if not self.has_table(table, database, cursor=cursor):
                raise ValueError("Table {!r} not exists in {!r}".format(table, database))
            cursor.execute(
                "SELECT * FROM {}.{} LIMIT 0".format(self.quote_identifier(database), self.quote_identifier(table))
            )
            cursor.fetchall()
            cols = self.get_columns_from_cursor(cursor)
        if exclude:
            cols = [x for x in cols if x not in exclude]
        return cols

    @staticmethod
    def get_columns_from_cursor(cursor):
        cols = []
        for item in cursor.description:
            name = item[0]
            if "." in name:
                cols.append(name.split(".")[1])
            else:
                cols.append(name)
        return cols

    def quote_identifier(self, v):
        parts = []
        for x in v.split("."):
            x = trim_prefix(x, self._identifier_start_quote)
            x = trim_suffix(x, self._identifier_end_quote)
            x = f"{self._identifier_start_quote}{x}{self._identifier_end_quote}"
            parts.append(x)
        return ".".join(parts)

    def cursor_to_schema(self, cursor):
        schema = Schema()
        for item in cursor.description:
            name = item[0]
            if "." in name:
                name = name.split(".")[1]

            type_code = item[1]
            size = item[3]

            ttype = self.to_canonical_type(type_code, size)
            schema.add_field_by_attrs(name, ttype, size)
        return schema

    @staticmethod
    def to_canonical_type(type_code, size):
        raise NotImplementedError()

    @staticmethod
    def from_canonical_type(canonical_type, size):
        raise NotImplementedError()

    def generate_create_table_ddl(self, name, schema, **kwargs):
        cols = []
        for f in schema:
            col_name = self.quote_identifier(f.name)
            if f.comment:
                cols.append(f"{col_name} {self.from_canonical_type(f.type, f.size)} COMMENT {f.comment!r}")
            else:
                cols.append(f"{col_name} {self.from_canonical_type(f.type, f.size)}")

        col_types = ",\n".join(cols)
        name = self.quote_identifier(name)
        ddl = f"CREATE TABLE {name} (\n{col_types}\n)"
        return ddl

    def generate_ddl(self, table, database=None, if_exists=True):
        raise NotImplementedError

    def load_csv_by_inserting(
        self,
        table,
        filename,
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        null_values=("NULL", r"\N"),
        null_replacer=None,
        batch_size=1000,
        values_hook=None,
        concurrency=1,
        **kwargs,
    ):
        csv_options = dict(
            delimiter=delimiter, quotechar=quotechar, lineterminator=lineterminator, escapechar=escapechar
        )
        csv_options.update(kwargs)

        if values_hook is None:
            values_hook = lambda x: x  # noqa: E731

        if concurrency <= 1:
            # fallback to use the main thread itself to avoid the overhead of queue
            self._insert_in_serial(
                table, filename, columns, csv_options, skiprows, null_values, null_replacer, batch_size, values_hook
            )
        else:
            self._insert_in_parallel(
                table,
                filename,
                columns,
                csv_options,
                skiprows,
                null_values,
                null_replacer,
                batch_size,
                values_hook,
                concurrency,
            )

    def _insert_in_serial(
        self,
        table,
        filename,
        columns,
        csv_options,
        skiprows=0,
        null_values=("NULL", r"\N"),
        null_replacer=None,
        batch_size=1000,
        values_hook=None,
    ):
        cursor = self.cursor()

        counter = TimeCounter(name="main", log_threshold=batch_size * 10, logger=self.logger)
        with open(filename, newline="") as fd:
            if skiprows:
                for _ in range(skiprows):
                    fd.readline()

            reader = csv.reader(fd, **csv_options)
            rows = []
            for row in reader:
                row = replace_null_values(row, null_values, null_replacer)
                row = values_hook(row)
                rows.append(row)
                counter.incr(1)
                if len(rows) == batch_size:
                    self._bulk_insert(cursor, table, columns, rows)
                    rows = []

            self._bulk_insert(cursor, table, columns, rows)

        counter.show_stat()
        cursor.close()

    def _insert_in_parallel(
        self,
        table,
        filename,
        columns,
        csv_options,
        skiprows=0,
        null_values=("NULL", r"\N"),
        null_replacer=None,
        batch_size=1000,
        values_hook=None,
        concurrency=1,
    ):
        data_queue = Queue(maxsize=2 * concurrency)
        exc_queue = Queue()
        # start workers
        workers = []
        for _ in range(concurrency):
            t = threading.Thread(target=self._write_worker, args=(table, columns, batch_size, data_queue, exc_queue))
            t.setDaemon(True)
            t.start()
            workers.append(t)

        # send tasks to queue
        counter = TimeCounter(name="main", log_threshold=batch_size * 10, logger=self.logger)
        with open(filename, newline="") as fd:
            if skiprows:
                for _ in range(skiprows):
                    fd.readline()

            reader = csv.reader(fd, **csv_options)

            rows = []
            for row in reader:
                row = replace_null_values(row, null_values, null_replacer)
                row = values_hook(row)
                counter.incr(1)
                rows.append(row)
                if len(rows) == batch_size:
                    while True:
                        try:
                            # wait up to 2 minutes before checking state of workers
                            # terminate immediately if any worker fails
                            data_queue.put(rows, block=True, timeout=120)
                        except Full:
                            if not exc_queue.empty():
                                raise RuntimeError(f"{exc_queue.qsize()} of {concurrency} workers failed")
                        else:
                            break
                    rows = []

            if rows:
                # this operation should not be fail in most cases
                data_queue.put(rows)

        self.logger.info("sending finish signal to all workers")
        for _ in workers:
            data_queue.put(None)

        self.logger.info("waiting for workers to exit")
        for t in workers:
            t.join()

        if not exc_queue.empty():
            raise RuntimeError(f"{exc_queue.qsize()} of {concurrency} workers failed")

        counter.show_stat()

    def _write_worker(self, table, cols, batch_size, data_queue: Queue, exc_queue: Queue):
        log_threshold = 5 * batch_size
        cursor = self.cursor()
        counter = TimeCounter(name="worker", log_threshold=log_threshold, logger=self.logger)
        while True:
            rows = data_queue.get()
            if rows is None:
                break

            # data_queue.task_done()
            counter.incr(len(rows))
            try:
                self._bulk_insert(cursor, table, cols, rows)
                rows = []
            except Exception as e:
                self.logger.exception("failed to insert %d rows, break", len(rows))
                # 发生异常就终止
                exc_queue.put(e)
                break

        counter.show_stat()
        cursor.close()
        self.logger.info("ready to exit.")

    def _bulk_insert(self, cursor, table, cols, rows):
        if not rows:
            return

        col_count = len(rows[0])

        if cols:
            field_names = "({})".format(", ".join([self.quote_identifier(x) for x in cols]))
        else:
            field_names = ""

        placeholders = ", ".join([self._param_placeholder] * col_count)
        sql = f"INSERT INTO {table} {field_names} VALUES ({placeholders})"

        cursor.executemany(sql, rows)
        cursor.connection.commit()

    def add_leading_comment(self, query, comment):
        tokens = []
        for q in sqlparse.split(query.strip()):
            tokens.append(self._add_leading_comment_impl(q.strip().rstrip(";"), comment))
        return ";\n".join(tokens)

    def _add_leading_comment_impl(self, query, comment):
        comment = self._safe_comment(comment)
        return "/* {} */\n{}".format(comment, query)

    def _safe_comment(self, comment):
        # 强行将 comment 中可能存在的 */ 或 /* 替换为 '', 以免 comment 失效报错
        comment = re.sub(pattern=r"\*\/|\/\*", repl="", string=comment)
        return ", ".join(comment.split("\n"))

    def is_mysql(self):
        return False

    def is_impala(self):
        return False

    def is_hive(self):
        return False

    def is_postgres(self):
        return False

    def is_redshift(self):
        return False

    def is_mssql(self):
        return False

    def is_azure_synapse(self):
        return False

    def is_clickhouse(self):
        return False

    def is_clickhouse_native(self):
        return False

    def is_phoenix(self):
        return False

    def is_google_bigquery(self):
        return False
