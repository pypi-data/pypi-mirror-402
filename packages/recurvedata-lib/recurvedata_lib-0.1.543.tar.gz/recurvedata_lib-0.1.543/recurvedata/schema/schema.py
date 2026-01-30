import dataclasses
from typing import Any

from recurvedata.schema.field import Field
from recurvedata.schema.types import DataType
from recurvedata.utils import json


@dataclasses.dataclass
class Schema:
    fields: list[Field] = dataclasses.field(default_factory=list)

    def add_field(self, field: Field):
        if field.name in self.field_names:
            raise ValueError(f"Field name {field.name} already exists")
        self.fields.append(field)

    def add_field_by_attrs(
        self,
        name: str,
        type: DataType,
        size: int = None,
        comment: str = None,
        extra: dict = None,
    ):
        self.add_field(Field(name, type, size, comment, extra))

    def remove_field(self, name: str):
        self.fields = [x for x in self.fields if x.name != name]

    def keep_fields(self, names: list[str]):
        self.fields = [x for x in self.fields if x.name in names]

    @property
    def field_names(self) -> list[str]:
        return [x.name for x in self.fields]

    def __iter__(self):
        return iter(self.fields)

    def to_list(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in self.fields]

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_list(), **kwargs)

    def dump(self, filename: str):
        with open(filename, "w") as f:
            f.write(self.to_json(indent=2))

    @classmethod
    def load(cls, filename: str) -> "Schema":
        with open(filename) as f:
            data = json.loads(f.read())
        return cls([Field(**item) for item in data])
