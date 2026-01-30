from typing import Any, Generic, TypeVar, cast

from pydantic import ValidationError

from recurvedata.filestorage.interface import AbstractFileStorage, StorageType
from recurvedata.utils.imports import import_string

_ST = TypeVar("_ST", bound=StorageType)
_SC = TypeVar("_SC", bound=AbstractFileStorage)


class Factory(Generic[_ST, _SC]):
    def __init__(self, implementations: dict[_ST, str]):
        self._implementations: dict[_ST, str] = implementations

    def get_supported_backends(self) -> list[_ST]:
        return list(self._implementations.keys())

    def get_storage_class(self, type_: _ST | str):
        return cast(type[_SC], import_string(self._implementations[type_]))

    def create(self, type_: _ST | str, options: dict[str, Any]) -> _SC:
        if type_ not in self._implementations:
            raise ValueError(f"Unsupported storage backend: {type_}")

        storage_class = self.get_storage_class(type_)

        try:
            obj = storage_class.from_params(**options)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration for {type_}: {e}")

        return obj
