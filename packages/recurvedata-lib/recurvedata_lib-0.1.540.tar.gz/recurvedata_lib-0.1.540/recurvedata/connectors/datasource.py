"""
之前 Pigeon 里叫法是 DataSource
这里先封装一个类似的，
之后再整合到 Base 里
"""

import copy
from dataclasses import dataclass
from typing import Optional

from recurvedata.connectors.const import DBAPI_TYPES, preprocess_conf


@dataclass
class DataSourceBase:
    connection_type: str
    data: dict
    name: str = ""
    extra: dict = None

    def __post_init__(self):
        self.data = preprocess_conf(self.connection_type, self.data)
        self.process_pigeon_keyword()
        self.extra = copy.deepcopy(self.data)

    def process_pigeon_keyword(self):
        """
        OneFlow 使用的是 pigeon 的关键词，部分和 Recurve 不一致。
        历史原因，从 OneFlow 迁移过来时，是直接复制数据库数据，没有转换关键词，
        导致 Recurve 数据库里同时存在两套。
        这里把旧的 pigeon 关键词转成新的 Recurve 关键词
        :return:
        """
        from recurvedata.connectors.pigeon import DataSource as PigeonDataSource

        keyword_renames: dict = PigeonDataSource.PIGEON_KEYWORD_MAPPING.get(self.connection_type, {})
        for recurve_keyword, pigeon_keyword in keyword_renames.items():
            if not pigeon_keyword or recurve_keyword in self.data or pigeon_keyword not in self.data:
                continue
            self.data[recurve_keyword] = self.data[pigeon_keyword]

    @property
    def recurve_connector_cls(self):
        from recurvedata.connectors._register import get_connection_class

        return get_connection_class(self.connection_type)

    @property
    def recurve_connector(self):
        """
        和 pigeon connector 区分开
        :return:
        """
        recurve_cls = self.recurve_connector_cls
        if not recurve_cls:
            raise ValueError(f"Unknown connection type: {self.connection_type}")
        recurve_con = recurve_cls(self.data)
        return recurve_con

    def juice_sync_path(self, path: str) -> tuple[str, str]:
        """
        Return the paths used in juice sync.
        The first return value is the path with a secret key,
        and the second return value is the path without a secret key, intended for display purposes
        """
        if not self.recurve_connector_cls:
            raise ValueError(f"{self.connection_type} is not juice sync able")
        return self.recurve_connector.juice_sync_path(path)


class DataSource(DataSourceBase):
    """
    pigeon 里 DataSource 等同于 Connection，这里保留两种叫法
    """

    @property
    def connector(self):
        """
        暂时保留之前 OneFlow 做法，返回 pigeon Connector 对象
        """
        from recurvedata.connectors.pigeon import DataSource as PigeonDataSource

        if PigeonDataSource.is_support_connection_type(self.connection_type):
            pigeon_ds = PigeonDataSource(connection_type=self.connection_type, name=self.name, data=self.data)
            return pigeon_ds.connector
        recurve_cls = self.recurve_connector_cls
        if not recurve_cls:
            raise ValueError(f"Unknown connection type: {self.connection_type}")
        recurve_con = recurve_cls(self.data)
        return recurve_con

    def create_engine(self):
        return self.connector.create_engine()

    @property
    def host(self):
        for key in ["url", "host"]:
            if key in self.data:
                return self.data[key]

    @property
    def ds_type(self):
        # 兼容 oneflow lineage
        return self.connection_type

    @property
    def database(self):
        # used in postgres load
        return self.data.get("database")

    @property
    def port(self):
        # used in email load
        return self.data.get("port")

    @property
    def password(self):
        # used in email load
        return self.data.get("password")

    @property
    def user(self):
        # used in email load
        return self.data.get("user")


class DataSourceWrapper(object):
    """封装 DataSource，只保留必要的只读功能"""

    def __init__(self, ds: DataSource):
        self.__ds = ds

    @property
    def name(self) -> str:
        return self.__ds.name

    @property
    def ds_type(self) -> str:
        return self.__ds.connection_type

    @property
    def host(self) -> Optional[str]:
        return self.__ds.host

    @property
    def database(self) -> Optional[str]:
        return self.__ds.database

    @property
    def user(self) -> Optional[str]:
        return self.__ds.user

    @property
    def password(self) -> Optional[str]:
        # 最初的设计里，ds_wrapper 不提供 password，但是后来使用的地方较多
        return self.__ds.password

    @property
    def port(self) -> Optional[int]:
        return self.__ds.port

    @property
    def is_dbapi(self) -> bool:
        return self.ds_type in DBAPI_TYPES

    @property
    def connector(self):
        return self.__ds.connector

    @property
    def recurve_connector(self):
        return self.__ds.recurve_connector

    @property
    def data(self) -> dict:
        if self.ds_type == "other":
            return self.__ds.data.get("data", self.__ds.data)
        return self.__ds.data

    @property
    def extra(self) -> dict:
        if self.ds_type == "other":
            return self.__ds.extra.get("data", self.__ds.extra)
        return self.__ds.extra

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]
        return super().__getattribute__(name)  # raise
