from typing import Any

from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.configurable import BaseConfigModel, Configurable
from recurvedata.utils.log import LoggingMixin


class BaseConnector(Configurable, LoggingMixin):
    """Abstract base class for connectors."""

    def __init__(self, config: BaseConfigModel, **kwargs):
        self.config = config
        self.kwargs = kwargs

        self._log_config_logger_name = "recurvedata.connectors"
        if kwargs.get("logger_name"):
            self._logger_name = kwargs.get("logger_name")

    def connect(self) -> Any:
        raise NotImplementedError("connect method not implemented")

    def test_connection(self) -> bool:
        raise NotImplementedError("test_connection method not implemented")


class RecurveConnectorBase(object):
    category: list[ConnectionCategory] = [
        ConnectionCategory.OTHERS,
    ]
    ui_category = ""
    setup_extras_require = []
    connection_type = ""
    ui_connection_type = ""
    config_schema = {}
    enabled = True
    juice_sync_able = False  # 是否可用于 juice sync 同步
    group: list[ConnectorGroup] = []
    test_required = True
    available_column_types = []

    def __init__(self, conf, *args, **kwargs):
        self.conf = conf
        self.args = args
        self.kwargs = kwargs

    def __getattribute__(self, key):  # todo: use s.attr
        try:
            return super().__getattribute__(key)
        except AttributeError as e:
            if key in self.conf:
                return self.conf[key]
            if key in self.kwargs:
                return self.kwargs[key]
            if key in self.connection_keys and key not in self.required_keys:
                return None
            raise e

    def test_connection(self):
        pass

    @classmethod
    def get_secret_keys(cls):
        return cls.config_schema.get("secret", [])

    @staticmethod
    def preprocess_conf(conf: dict) -> dict:
        """
        在connector 对象初始化之前，调用这个函数，处理一下 conf，
        原因：
        1. 有些 json 数据存到数据库后，是 txt 字段，这里处理下
        2. 增加一些通用的字段 mapping
        :return: dict
        """
        if "passwd" in conf:
            conf["password"] = conf["passwd"]
        return conf

    required_keys = []  # todo: cache property from config_schema
    connection_keys = []

    def juice_sync_path(self, path: str) -> tuple[str, str]:
        """
        Return the paths used in juice sync.
        The first return value is the path with a secret key,
        and the second return value is the path without a secret key, intended for display purposes.
        """
        if not self.juice_sync_able:
            raise ValueError(f"{self.connection_type} is not juice sync able")
        raise NotImplementedError

    @classmethod
    def format_config_schema(cls):
        return cls.config_schema

    @classmethod
    def is_dbt_supported(cls):
        from recurvedata.connectors.const import DBT_SUPPORTED_TYPES

        return cls.connection_type in DBT_SUPPORTED_TYPES

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict:
        raise NotImplementedError("convert_config_to_dbt_profile method not implemented")

    @classmethod
    def is_cube_supported(cls):
        from recurvedata.connectors.const import CUBE_SUPPORTED_TYPES

        return cls.connection_type in CUBE_SUPPORTED_TYPES

    def convert_config_to_cube_config(self, database: str = None, schema: str = None, ds = None) -> dict:
        raise NotImplementedError("convert_config_to_cube method not implemented")
