from __future__ import annotations

import datetime
import inspect
import logging
from typing import Optional, Type, TypeVar, Union

import pendulum

_T = TypeVar("_T")


# This is a copy of the airflow.utils.log.logging_mixin.LoggingMixin class
class LoggingMixin:
    """Convenience super-class to have a logger configured with the class name."""

    _log: Optional[logging.Logger] = None

    # Parent logger used by this class. It should match one of the loggers defined in the
    # `logging_config_class`. By default, this attribute is used to create the final name of the logger, and
    # will prefix the `_logger_name` with a separating dot.
    _log_config_logger_name: Optional[str] = None  # noqa: UP007

    _logger_name: Optional[str] = None  # noqa: UP007

    @staticmethod
    def _create_logger_name(
        logged_class: Type[_T],
        log_config_logger_name: str = None,
        class_logger_name: str = None,
    ) -> str:
        """Generate a logger name for the given `logged_class`.

        By default, this function returns the `class_logger_name` as logger name. If it is not provided,
        the {class.__module__}.{class.__name__} is returned instead. When a `parent_logger_name` is provided,
        it will prefix the logger name with a separating dot.
        """
        logger_name: str = (
            class_logger_name if class_logger_name is not None else f"{logged_class.__module__}.{logged_class.__name__}"
        )

        if log_config_logger_name:
            return f"{log_config_logger_name}.{logger_name}" if logger_name else log_config_logger_name
        return logger_name

    @classmethod
    def _get_log(cls, obj: Union["LoggingMixin", Type["LoggingMixin"]], clazz: Type[_T]) -> logging.Logger:
        if obj._log is None:
            logger_name: str = cls._create_logger_name(
                logged_class=clazz,
                log_config_logger_name=obj._log_config_logger_name,
                class_logger_name=obj._logger_name,
            )
            obj._log = logging.getLogger(logger_name)
        return obj._log

    @classmethod
    def logger(cls) -> logging.Logger:
        """Return a logger."""
        return LoggingMixin._get_log(cls, cls)

    @property
    def log(self) -> logging.Logger:
        """Return a logger."""
        return LoggingMixin._get_log(self, self.__class__)


class AwareFormatter(logging.Formatter):
    _local_tz = pendulum.local_timezone()

    def formatTime(self, record, datefmt=None):
        # Use dateutil to get a timezone-aware datetime
        dt = datetime.datetime.fromtimestamp(record.created, tz=self._local_tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def init_logging(
    level=logging.INFO,
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - [%(process)d:%(threadName)s] - %(message)s",
):
    logging.basicConfig(level=level, format=fmt)

    logging.getLogger("httpx").setLevel(logging.WARNING)


def setup_loguru():
    class InterceptHandler(logging.Handler):
        """Intercept standard logging messages and redirect them to loguru.""" ""

        def emit(self, record):
            from loguru import logger

            level: str | int
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message.
            frame, depth = inspect.currentframe(), 0
            while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    # logging.root.setLevel(logging.INFO)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
