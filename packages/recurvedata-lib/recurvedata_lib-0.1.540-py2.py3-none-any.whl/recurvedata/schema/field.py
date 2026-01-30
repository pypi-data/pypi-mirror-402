import dataclasses
import datetime
from typing import Any, Callable, Optional

import dateutil.parser

from recurvedata.schema.types import DataType
from recurvedata.utils import json
from recurvedata.utils.registry import GenericRegistry

_registry = GenericRegistry[DataType, Callable[[str], Any]]()


@_registry.add(DataType.INT8, DataType.INT16, DataType.INT32, DataType.INT64)
def _(value: str) -> int:
    if value == "":
        return 0
    return int(value)


@_registry.add(DataType.FLOAT32, DataType.FLOAT64)
def _(value: str) -> float:
    if value == "":
        return 0.0
    return float(value)


@_registry.add(DataType.BOOLEAN)
def _(value: str) -> bool:
    if value.lower() in ("", "0", "false"):
        return False
    return True


@_registry.add(DataType.DATETIME)
def _(value: str) -> Optional[datetime.datetime]:
    if value == "":
        return None
    return dateutil.parser.parse(value)


@_registry.add(DataType.DATE)
def _(value: str) -> Optional[datetime.date]:
    if value == "":
        return None
    return dateutil.parser.parse(value).date()


@_registry.add(DataType.JSON)
def _(value: str) -> Any:
    if value in ("",):
        # 正常情况下不会有 ''，很可能是从 CSV 文件读到了空字符，当作 None 处理
        return None
    return json.loads(value)


@dataclasses.dataclass
class Field:
    name: str
    type: DataType
    size: int = None
    comment: str = None
    extra: dict = None

    def __post_init__(self):
        self._cast_func: Callable[[str], Any] = _registry.get(self.type, lambda x: x)

    def cast(self, value: Optional[str]) -> Any:
        if value is None:
            return None
        if value == "NULL":
            return None
        return self._cast_func(value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "comment": self.comment,
            "extra": self.extra,
        }

    def __str__(self):
        return f'<Field ("{self.name}", "{self.type}")>'

    def __repr__(self):
        return f'<Field ("{self.name}", "{self.type}")>'
