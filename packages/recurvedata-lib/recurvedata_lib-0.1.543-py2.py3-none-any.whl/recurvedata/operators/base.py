from typing import Any

import jsonschema

from recurvedata.core.translation import convert_lazy_string


class Configurable(object):
    enabled = True

    @classmethod
    def config_schema(cls) -> dict:
        return {}

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def to_dict(cls) -> dict:
        return {"name": cls.name(), "config_schema": cls.config_schema()}

    @classmethod
    def validate(cls, configuration: dict[str, Any]) -> dict[str, Any]:
        schema = cls.config_schema()
        schema = convert_lazy_string(schema)
        jsonschema.validate(configuration, schema)
        return configuration
