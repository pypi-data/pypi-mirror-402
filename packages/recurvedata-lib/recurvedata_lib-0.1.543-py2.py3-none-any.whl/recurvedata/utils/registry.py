from typing import Callable, Generic, ItemsView, Iterable, KeysView, TypeVar, Union, ValuesView

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class GenericRegistry(Generic[_KT, _VT]):
    def __init__(self):
        self._registry: dict[_KT, _VT] = {}

    def add(self, *keys: _KT) -> Callable[[_VT], _VT]:
        def inner(target: _VT) -> _VT:
            for k in keys:
                self._registry[k] = target
            return target

        return inner

    def get(self, key: _KT, default: _VT = None) -> _VT:
        return self._registry.get(key, default)

    def __len__(self) -> int:
        return len(self._registry)

    def keys(self) -> KeysView[_KT]:
        return self._registry.keys()

    def values(self) -> ValuesView[_VT]:
        return self._registry.values()

    def items(self) -> ItemsView[_KT, _VT]:
        return self._registry.items()

    def __getitem__(self, key):
        return self._registry.get(key)


class Registry(GenericRegistry[str, _VT]):
    def __init__(self, key_callback: Callable[[_VT], Union[str, Iterable[str]]]):
        self.key_callback = key_callback
        super().__init__()

    def add(self, target: _VT) -> _VT:
        keys: Union[str, Iterable[str]] = self.key_callback(target)
        if isinstance(keys, str):
            keys = [keys]
        return super().add(*keys)(target)

    def register(self, target: _VT) -> _VT:  # Compatibility with recurvedata.operator
        return self.add(target)


jinja2_template_funcs_registry = Registry(key_callback=lambda x: x.__name__)
register_func = jinja2_template_funcs_registry.add
