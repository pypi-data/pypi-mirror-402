from typing import List

from recurvedata.pigeon.handler.base import Handler, HandlerFactory
from recurvedata.pigeon.meta import DumperMeta, DumperWorkerMeta
from recurvedata.pigeon.row_factory import keyed_tuple_factory
from recurvedata.pigeon.utils import LoggingMixin, ensure_list
from recurvedata.pigeon.utils.timing import Timer


class BaseWorker(LoggingMixin):
    def __init__(self, worker_id, task_id, handlers, row_factory=keyed_tuple_factory, retries=3):
        self.worker_id = worker_id
        self.task_id = task_id
        self.handlers = handlers
        self.row_factory = row_factory
        self.retries = retries
        self.meta = DumperWorkerMeta()

    def _log(self, msg, *args, **kwargs):
        msg = f'Worker#{self.worker_id} Task#{self.task_id} {msg}'
        self.logger.info(msg, *args, **kwargs)

    def call_handlers(self, row):
        for h in self.handlers:
            # the handlers should take care of exceptions
            h.handle(row)

    def close_handlers(self):
        for h in self.handlers:
            h.close()

    def reset_handlers(self):
        self._log('reset handlers')
        for h in self.handlers:
            h.reset()

    def set_input_schema(self, schema):
        self.meta.schema = schema
        for h in self.handlers:
            h.set_input_schema(schema)

    def execute(self):
        self._log('executing')
        for i, h in enumerate(self.handlers):
            self._log('Handler #%s: %s', i, h)

        for num_try in range(self.retries):
            self._log(f'Try#{num_try}')
            try:
                rv = self.execute_impl()
            except Exception as ex:
                self._log(str(ex))
                self.logger.exception(ex)
                self.reset_handlers()
            else:
                break
        else:
            # TODO(liyangliang): 使用自定义的异常
            raise RuntimeError('All attempts failed')
        self.close_handlers()

        self.meta.num_dumped_rows = rv
        self.meta.handlers_meta = [x.meta for x in self.handlers]
        return self.meta

    def execute_impl(self):
        raise NotImplementedError('execute_impl must be implemented by subclass')

    def start_timer(self):
        return Timer(logger=self.logger)


class SQLBasedWorker(BaseWorker):
    def __init__(self, connector, query, parameters, handlers, *args, **kwargs):
        self.connector = connector
        self.query = query
        self.parameters = parameters
        super().__init__(handlers=handlers, *args, **kwargs)

    def execute_impl(self):
        n = 0
        t = self.start_timer()
        for row in self.dump_query(self.query, self.parameters):
            self.call_handlers(row)
            n += 1
            if n % 10000 == 0:
                t.info('dumped %d rows', n)
        t.info('dumped %d rows in total', n)
        return n

    def dump_query(self, query, parameters):
        raise NotImplementedError('dump_query must be implemented by subclass')


class BaseDumper(LoggingMixin):
    _row_factory = staticmethod(keyed_tuple_factory)

    def __init__(self, handler_factories, *args, **kwargs):
        self.handler_factories = ensure_list(handler_factories or [])

        assert len(self.handler_factories) > 0, 'must specific at least one HandlerFactory'
        for hf in self.handler_factories:
            assert isinstance(hf, HandlerFactory)

        self.meta = DumperMeta()

    @property
    def row_factory(self):
        """
        The format to return row results in. By default, each returned row will be a named tuple.
        You can alternatively use any of the following:

          - :func:`pigeon.row_factory.tuple_factory` - return a result row as a tuple
          - :func:`pigeon.row_factory.keyed_tuple_factory` - return a result row as a named tuple
          - :func:`pigeon.row_factory.dict_factory` - return a result row as a dict
          - :func:`pigeon.row_factory.ordered_dict_factory` - return a result row as an OrderedDict
        """
        return self._row_factory

    @row_factory.setter
    def row_factory(self, factory):
        self._row_factory = factory

    def create_handlers(self, **kwargs) -> List[Handler]:
        return [hf.create_handler(**kwargs) for hf in self.handler_factories]

    def join_handlers(self):
        [hf.join() for hf in self.handler_factories]

    def handle_schema(self):
        return [hf.handle_dumper_schema(self.meta.schema) for hf in self.handler_factories]

    def set_input_schema(self, schema):
        for hf in self.handler_factories:
            hf.transformer.input_schema = schema

    def execute(self):
        raise NotImplementedError('execute must be implemented by subclass')

    def start_timer(self):
        return Timer(logger=self.logger)
