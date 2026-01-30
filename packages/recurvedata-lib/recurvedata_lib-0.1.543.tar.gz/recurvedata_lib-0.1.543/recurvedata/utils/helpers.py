import hashlib
import os
from typing import Callable, Generator, Iterable, TypeVar, Union, overload

import cytoolz as toolz

from recurvedata.consts import ENV_ID_KEY

T = TypeVar("T")
_VT = TypeVar("_VT")
_KT = TypeVar("_KT")


# Hash helpers


def _get_hash(v: Union[str, bytes], hash_func: Callable) -> str:
    if isinstance(v, str):
        v = v.encode()
    if not isinstance(v, bytes):
        v = str(v).encode()
    return hash_func(v).hexdigest()


def sha256hash(v: Union[str, bytes]) -> str:
    return _get_hash(v, hashlib.sha256)


def md5hash(v: Union[str, bytes]) -> str:
    return _get_hash(v, hashlib.md5)


# String helpers


def trim_prefix(s: str, sub: str) -> str:
    if not s.startswith(sub):
        return s
    return s[len(sub) :]


def trim_suffix(s: str, sub: str) -> str:
    if not s.endswith(sub):
        return s
    return s[: -len(sub)]


def truncate_string(s: str, length: int, replacer: str = "...") -> str:
    if len(s) > length:
        return s[:length] + replacer
    return s


def unescape_backslash(s: str) -> str:
    return s.encode().decode("unicode_escape")


def safe_int(v: Union[str, int, float], default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def safe_float(v: Union[str, int, float], default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


# Container helpers


def first(seq: Iterable[T], default: T = None) -> T:
    try:
        return toolz.first(seq)
    except StopIteration:
        return default


def chunkify(lst: list, size: int) -> Generator[list, None, None]:
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def extract_dict(d: dict[_KT, _VT], keys: Iterable[_KT]) -> dict[_KT, _VT]:
    return {k: v for k, v in d.items() if k in keys}


def ensure_list(v: Union[T, Iterable[T]]) -> list[T]:
    if isinstance(v, (tuple, set, list)):
        return list(v)
    return [v]


def ensure_str_list(v: str, sep: str = ",", strip: bool = True) -> list[str]:
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


@overload
def replace_null_values(
    row: list[T],
    null_values: Union[list[T], set[T]],
    replacer: T = None,
) -> list[T]:
    ...


@overload
def replace_null_values(
    row: tuple[T, ...],
    null_values: Union[list[T], set[T]],
    replacer: T = None,
) -> tuple[T, ...]:
    ...


@overload
def replace_null_values(
    row: dict[_KT, _VT],
    null_values: Union[list[_VT], set[_VT]],
    replacer: _VT = None,
) -> dict[_KT, _VT]:
    ...


def replace_null_values(
    row: Union[list[_VT], tuple[_VT, ...], dict[_KT, _VT]],
    null_values: Union[list[_VT], set[_VT]],
    replacer: _VT = None,
) -> Union[list[_VT], tuple[_VT, ...], dict[_KT, _VT]]:
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


def get_env_id():
    return int(os.environ[ENV_ID_KEY])


def get_environment_variable(key: str, cast: Callable[[str], T] | None = None) -> T | None:
    value = os.environ.get(key)
    if value is None:
        return None
    if cast is not None:
        return cast(value)
    return value
