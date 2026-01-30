from typing import Any, KeysView, Union


class AttrDict(dict):
    """A dict that allows for attribute-style access."""

    def __getattr__(self, item: str) -> Union[Any, "AttrDict"]:
        if item not in self:
            return None
        value = self[item]
        if isinstance(value, dict):
            return AttrDict(value)
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __dir__(self) -> KeysView[str]:
        return self.keys()
