import cytoolz as toolz

from recurvedata.pigeon.meta import HandlerFactoryMeta, HandlerMeta
from recurvedata.pigeon.transformer import Transformer
from recurvedata.pigeon.utils import LoggingMixin

_default_transformer = Transformer()


class Handler(LoggingMixin):
    ERROR_HANDLE_PARAMS = [
        "max_error_rate",
        "min_sample_rows",
        "check_error_rate_on_finish",
        "max_continuous_error_log_rows",
        "max_continuous_error_log_size",
        "error_log_cycle_interval",
    ]

    def __init__(
        self,
        transformer=_default_transformer,
        max_error_rate=0.2,
        min_sample_rows=1000,
        check_error_rate_on_finish=True,
        max_continuous_error_log_rows=10,
        max_continuous_error_log_size=500000,
        error_log_cycle_interval=100,
        *args,
        **kwargs,
    ):
        """记录处理逻辑，接收一行输入，调用转换逻辑，输出处理结果。
        :param transformer: 定义数据处理逻辑，Transformer 或子类对象
        :param max_error_rate: 最大错误率，超出该错误率可能会（结合样本大小）抛出异常中断程序
        :param min_sample_rows: 最小采样数量，避免样本太小导致误报
        :param check_error_rate_on_finish: 在程序结束时检查错误率，达到阈值会抛出异常，避免因为数据量太小达不到样本容量而淹没错误。
        :param max_continuous_error_log_rows: 单个 handler 连续打印的报错 row 的最大行数，防止错误日志太多 log 太大
        :param max_continuous_error_log_size: 单个 handler 连续打印的报错 row 字符串的最大字符数，默认 50w, 防止错误日志太多 log 太大
        "param error_log_cycle_interval: 当达到单个 handler 连续打印最大行数或者最大字符数后，仍然间隔 error_log_cycle_interval 打印一次报错日志
        """
        self.transformer = transformer
        self.max_error_rate = max_error_rate
        self.min_sample_rows = min_sample_rows
        self.check_error_rate_on_finish = check_error_rate_on_finish
        self.max_continuous_error_log_rows = max_continuous_error_log_rows
        self.max_continuous_error_log_size = max_continuous_error_log_size
        self.error_log_cycle_interval = error_log_cycle_interval

        self.meta = HandlerMeta()
        self.meta.schema = self.transformer.output_schema

    def set_transformer(self, transformer):
        self.transformer = transformer

    def transform(self, row):
        return self.transformer.transform(row)

    def set_input_schema(self, schema):
        self.transformer.input_schema = schema

    def close(self):
        if self.check_error_rate_on_finish:
            self.check_error_rate()

    def emit(self, row):
        raise NotImplementedError("emit must be implemented by subclasses")

    def handle(self, row):
        self.meta.num_input_rows += 1
        try:
            rv = self.transform(row)
            if rv:
                num_rows = self.emit(rv)
                self.meta.num_output_rows += num_rows
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handle_error(row)

        if self.meta.num_input_rows >= self.min_sample_rows:
            self.check_error_rate()

    @property
    def error_rate(self):
        if self.meta.num_input_rows == 0:
            return 0
        return self.meta.num_error_rows / self.meta.num_input_rows

    def check_error_rate(self):
        if self.error_rate > self.max_error_rate:
            raise RuntimeError(
                f"max_error_rate reached,"
                f" #input: {self.meta.num_input_rows},"
                f" #error: {self.meta.num_error_rows},"
                f" error_rate: {self.error_rate},"
                f" threshold: {self.max_error_rate}"
            )

    def handle_error(self, row):
        self.meta.num_error_rows += 1
        self.meta.error_log_size += len(str(row))
        if (
            self.meta.num_error_rows <= self.max_continuous_error_log_rows
            and self.meta.error_log_size <= self.max_continuous_error_log_size
        ):
            self.logger.exception("failed to handle row: %s", row)
        elif self.meta.num_error_rows % self.error_log_cycle_interval == 0:
            self.logger.exception(
                "current handler total %s error rows, failed to handle row: %s", self.meta.num_error_rows, row
            )

    def reset(self):
        """reset all states"""
        self.meta.reset()


class NullHandler(Handler):
    def transform(self, row):
        pass

    def emit(self, row):
        pass

    def handle(self, row):
        return 0


class HandlerFactory(LoggingMixin):
    def __init__(self, handler_class, transformer=_default_transformer, **handler_options):
        self.handler_class = handler_class
        self.transformer = transformer
        self.handler_options = handler_options
        self.handlers = []

        self.meta = HandlerFactoryMeta(name=self.meta_name())

    def set_transformer(self, transformer):
        self.transformer = transformer

    def create_handler(self, **kwargs):
        h = self.handler_class(**toolz.merge(self.handler_options, kwargs))
        h.set_transformer(self.transformer)
        self.handlers.append(h)
        return h

    def join(self):
        pass

    def meta_name(self):
        return f"<{self.__class__.__name__}>"

    def handle_dumper_schema(self, schema):
        pass
