import datetime
import functools
import logging
import time

from recurvedata.utils.imports import MockModule

try:
    import humanize
except ImportError:
    humanize = MockModule("humanize")

_logger = logging.getLogger(__name__)


def time_since(dt):
    return datetime.datetime.now() - dt


class Timer(object):
    def __init__(self, delay=False, logger=None):
        self.logger = logger or _logger
        self.start_dttm = None
        if not delay:
            self.reset()

    def reset(self):
        self.start_dttm = datetime.datetime.now()

    def debug(self, message, *args):
        self._log(self.logger.debug, message, *args)

    def info(self, message, *args):
        self._log(self.logger.info, message, *args)

    def warning(self, message, *args):
        self._log(self.logger.warning, message, *args)

    def error(self, message, *args):
        self._log(self.logger.error, message, *args)

    def _log(self, func, message, *args):
        message = message.rstrip() + " took %s"
        # TODO: humanize timedelta
        args = args + (time_since(self.start_dttm),)
        func(message, *args)


class timing(object):
    def __init__(self, operation="", logger=None):
        self.operation = operation
        self._timer = Timer(delay=True, logger=logger)

    def __call__(self, func):
        if not self.operation:
            self.operation = "calling {}".format(func)

        @functools.wraps(func)
        def inner(*args, **kwargs):
            self._timer.reset()
            rv = func(*args, **kwargs)
            self._timer.info(self.operation)
            return rv

        return inner

    def __enter__(self):
        self._timer.reset()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._timer.info(self.operation or "operation finished")


class TimeCounter(object):
    def __init__(self, name="", log_threshold=5000, total=None, logger=None):
        self.name = name
        self.log_threshold = log_threshold
        self.total = total

        self._logger = logger or logging
        self._count = 0
        self._start_time = datetime.datetime.now()

    @property
    def count(self):
        return self._count

    def incr(self, by=1):
        self._count += by
        if self.log_threshold and self._count % self.log_threshold == 0:
            self.show_stat()

    def show_stat(self):
        d = datetime.datetime.now() - self._start_time
        speed = self._count / d.total_seconds()
        if not self.total:
            self._logger.info("<%s> finished %d in %s, speed: %.2f/s", self.name, self._count, d, speed)
        else:
            progress = 100.0 * self._count / self.total
            self._logger.info(
                "<%s> finished %d in %s, speed: %.2f/s, progress: %.2f", self.name, self._count, d, speed, progress
            )


class DisplayProgress:
    def __init__(self, total_amount: int = None, display_interval: float = 1024 * 1024, stream: bool = True):
        self._stream = stream
        self._seen_so_far = 0
        self._interval = display_interval
        self._start_time = datetime.datetime.now()
        self._size = total_amount

    def __call__(self, bytes_amount: int, total_amount: int = None):
        if self._stream:
            self._seen_so_far += bytes_amount
        else:
            self._seen_so_far = bytes_amount

        total_amount = total_amount or self._size
        if total_amount != 0:
            progress = (self._seen_so_far / total_amount) * 100
        else:
            progress = 0

        if not self._seen_so_far or (self._seen_so_far < total_amount and self._seen_so_far % self._interval != 0):
            return None

        duration = datetime.datetime.now() - self._start_time
        speed = self._seen_so_far / duration.total_seconds()
        _logger.info(
            "transferred %s in %s, average speed: %s/s, progress: %.2f%%",
            humanize.naturalsize(self._seen_so_far, gnu=True),
            duration,
            humanize.naturalsize(speed, gnu=True),
            progress,
        )


class ProgressCallback:
    def __init__(self):
        self._start_time = time.time()

    def __call__(self, consumed_bytes, total_bytes):
        if not total_bytes:
            return
        duration = time.time() - self._start_time
        speed = consumed_bytes / duration
        progress = 100 * (float(consumed_bytes) / float(total_bytes))
        logging.info(
            "transferred %s of %s,  avg speed: %s/s, progress: %.2f%%",
            humanize.naturalsize(consumed_bytes, gnu=True),
            humanize.naturalsize(total_bytes, gnu=True),
            humanize.naturalsize(speed, gnu=True),
            progress,
        )
