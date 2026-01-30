import hashlib
import logging
import time
from contextlib import contextmanager
from typing import Dict, List, Set, Tuple, TypeVar, Union
from uuid import uuid4

import cytoolz as toolz

logger = logging.getLogger(__name__)

T = TypeVar("T")


def safe_int(v: Union[str, int, float], default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def trim_prefix(s: str, sub: str) -> str:
    if not s.startswith(sub):
        return s
    return s[len(sub) :]


def trim_suffix(s: str, sub: str) -> str:
    if not s.endswith(sub):
        return s
    return s[: -len(sub)]


class LoggingMixin(object):
    @property
    def logger(self) -> logging.Logger:
        try:
            return self._logger
        except AttributeError:
            self._logger = logging.root.getChild(self.__class__.__module__ + "." + self.__class__.__name__)
            return self._logger


def init_logging(
    level_name="info",
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - [%(process)d:%(threadName)s] - %(message)s",
    silent_cassandra=True,
):
    level = logging.INFO
    if level_name == "info":
        level = logging.INFO
    elif level_name == "warning":
        level = logging.WARNING
    elif level_name == "error":
        level = logging.ERROR
    elif level_name == "debug":
        level = logging.DEBUG
    logging.basicConfig(level=level, format=fmt)

    if silent_cassandra:
        # cassandra is too noisy
        logging.getLogger("cassandra.cluster").setLevel(logging.WARNING)


def ensure_list(v: Union[T, Tuple[T], List[T], Set[T]]) -> List[T]:
    if isinstance(v, (tuple, set, list)):
        return list(v)
    return [v]


def ensure_str_list(v: str, sep: str = ",", strip: bool = True) -> List[str]:
    if v is None:
        return []

    if isinstance(v, str):
        if not v:
            return []
        if strip:
            return [x.strip() for x in v.split(sep)]
        else:
            return v.split(sep)

    if isinstance(v, (tuple, set, list)):
        return list(v)
    raise TypeError(f'unsupported type "{type(v)}"')


def ensure_query_list(v: Union[str, List[str]]) -> List[str]:
    if not v:
        return []
    if isinstance(v, list):
        return v
    return list(filter(None, map(lambda x: x.strip(), v.split(";"))))


def extract_dict(d: Dict, keys: List) -> Dict:
    return {k: v for k, v in d.items() if k in keys}


@contextmanager
def silent(*_excs, excs=None):
    excs = excs or _excs or (Exception,)
    try:
        yield
    except excs as e:
        logging.exception("silent %s", type(e).__name__)


def replace_null_values(row: Union[List, Tuple, Dict], null_values: List, replacer=None):
    def _f(v):
        if v in null_values:
            return replacer
        return v

    if isinstance(row, list):
        return list(map(_f, row))
    if isinstance(row, tuple):
        return tuple(map(_f, row))
    if isinstance(row, dict):
        return toolz.valmap(_f, row)
    raise TypeError(f"only list, tuple or dict type is supported, got {repr(type(row))}")


def md5hash(v: Union[str, bytes]) -> str:
    if isinstance(v, str):
        v = v.encode()
    if not isinstance(v, bytes):
        v = str(v).encode()
    return hashlib.md5(v).hexdigest()


def randomized_suffix() -> str:
    pure_time_str = str(time.time()).replace(".", "")
    return pure_time_str[-1] + uuid4().hex[:6]
