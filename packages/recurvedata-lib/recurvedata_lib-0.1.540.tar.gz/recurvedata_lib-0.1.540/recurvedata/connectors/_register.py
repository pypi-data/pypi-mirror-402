from typing import TYPE_CHECKING, Type, Union

from recurvedata.connectors.const import get_module_name

if TYPE_CHECKING:
    from recurvedata.connectors.base import RecurveConnectorBase

_registry = {}


def get_connection_class(connection_type: str, only_enabled=True) -> Type["RecurveConnectorBase"]:
    if connection_type not in _registry:
        module_name = get_module_name(connection_type)
        if module_name:
            __import__(module_name)

    cls = _registry.get(connection_type)
    if not only_enabled:
        return cls
    if cls and cls.enabled:
        return cls


class register_connector_class(object):  # todo: use meta class
    def __init__(self, connection_types: Union[str, list[str]]):
        if isinstance(connection_types, str):
            connection_types = [
                connection_types,
            ]
        self.connection_types: list = connection_types

    def __call__(self, connector_cls):
        for name in self.connection_types:
            _registry[name] = connector_cls
        self.add_connection_type(connector_cls)
        self.set_connection_keys(connector_cls)
        return connector_cls

    def add_connection_type(self, connection_cls):
        if not connection_cls.connection_type:
            connection_cls.connection_type = self.connection_types[0]

    def set_connection_keys(self, connection_cls):
        connection_cls.required_keys = connection_cls.config_schema.get("required", [])
        connection_cls.connection_keys = connection_cls.config_schema.get("order", [])
        connection_cls.secret_keys = connection_cls.config_schema.get("secret", [])
