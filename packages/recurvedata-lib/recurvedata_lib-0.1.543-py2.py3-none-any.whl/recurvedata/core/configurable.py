from typing import Any, ClassVar, Union

from pydantic import BaseModel, ConfigDict


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Configurable:
    config_model: ClassVar[BaseConfigModel]

    @classmethod
    def config_schema(cls) -> dict[str, Any]:
        return cls.config_model.model_json_schema()

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {"name": cls.name(), "config_schema": cls.config_schema()}

    @classmethod
    def validate(cls, configuration: Union[dict, BaseConfigModel]) -> BaseConfigModel:
        return cls.config_model.model_validate(configuration)
