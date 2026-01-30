"""
使用 pigeon connector 作为底层实现
返回 pigeon connector
"""

import copy
import os

from recurvedata.connectors.datasource import DataSourceBase


class DataSource(DataSourceBase):
    """
    pigeon 里 DataSource 等同于 Connection，这里保留两种叫法
    """

    def __post_init__(self):
        super().__post_init__()
        keyword_renames: dict = self.PIGEON_KEYWORD_MAPPING.get(self.connection_type, {})
        for recurve_keyword, pigeon_keyword in keyword_renames.items():
            val = self.data.pop(recurve_keyword, None)
            if pigeon_keyword:
                self.data[pigeon_keyword] = val
                self.extra[pigeon_keyword] = self.extra.get(recurve_keyword)
        if "passwd" in self.data:
            self.data["password"] = self.data["passwd"]
            self.extra["password"] = self.extra["passwd"]
        if self.connection_type == "bigquery":
            self.data["dataset"] = self.data.get("database")
            if "key_dict" not in self.data:
                # some are not saved through the web page, have key_dict field, no need to modify
                key_dict = copy.deepcopy(self.data)
                key_dict.pop("location", None)
                key_dict.pop("proxies", None)
                self.data["key_dict"] = key_dict
                self.extra["key_dict"] = key_dict
        if self.connection_type == "sftp":
            pk_path = self.data.get("rsa_private_key_file")
            if pk_path == "":
                self.data.pop("rsa_private_key_file")
            elif pk_path:
                self.data["rsa_private_key_file"] = os.path.expanduser(pk_path)
                self.extra["rsa_private_key_file"] = os.path.expanduser(pk_path)

    PIGEON_KEYWORD_MAPPING = {
        "s3": {"access_key_id": "aws_access_key_id", "secret_access_key": "aws_secret_access_key", "bucket": None},
        "filebrowser": {"url": "host"},
        "kafka": {
            "bootstrap_servers": "bootstrap.servers",
            "value_deserializer": "value.deserializer",
            "value_schema_registry_client_url": "schema_registry_client_url",
        },
        "oss": {"secret_access_key": "access_key_secret", "access_key_id": "access_key_id", "bucket": "bucket_name"},
        "sftp": {"user": "username", "private_key_path": "rsa_private_key_file"},
        "mongodb": {"user": "username"},
        "bigquery": {"database": "dataset"},
    }

    PIGEON_TYPE_CLS_MAPPING = {
        "s3": "recurvedata.pigeon.connector.awss3",
        "oss": "recurvedata.pigeon.connector.aliyun_oss",
        "azure_blob": "recurvedata.pigeon.connector.azure_blob",
        "azure_synapse": "recurvedata.pigeon.connector.azure_synapse",
        "clickhouse": "recurvedata.pigeon.connector.clickhouse_native",
        "es": "recurvedata.pigeon.connector.es",
        "ftp": "recurvedata.pigeon.connector.ftp",
        "google_bigquery": "recurvedata.pigeon.connector.google_bigquery",
        "phoenix": "recurvedata.pigeon.connector.hbase_phoenix",
        "hdfs": "recurvedata.pigeon.connector.hdfs",
        "hive": "recurvedata.pigeon.connector.hive_impala",
        "impala": "recurvedata.pigeon.connector.hive_impala",
        "mongodb": "recurvedata.pigeon.connector.mongodb",
        "mssql": "recurvedata.pigeon.connector.mssql",
        "mysql": "recurvedata.pigeon.connector.mysql",
        "postgresql": "recurvedata.pigeon.connector.postgresql",
        "postgres": "recurvedata.pigeon.connector.postgresql",
        "qcloud_cos": "recurvedata.pigeon.connector.qcloud_cos",
        "cos": "recurvedata.pigeon.connector.qcloud_cos",
        "redshift": "recurvedata.pigeon.connector.redshift",
        "sftp": "recurvedata.pigeon.connector.sftp",
        "owncloud": "recurvedata.pigeon.connector.owncloud",
        "starrocks": "recurvedata.pigeon.connector.starrocks",
        "doris": "recurvedata.pigeon.connector.doris",
        "microsoft_fabric": "recurvedata.pigeon.connector.microsoft_fabric",
    }

    PIGEON_TYPE_MAPPING = {
        "tidb": "mysql",
        "bigquery": "google_bigquery",
    }

    @property
    def connector(self):
        """
        暂时保留之前 OneFlow 做法，返回 pigeon Connector 对象
        """
        return self.get_pigeon_connector()

    def create_engine(self):
        return self.connector.create_engine()

    def get_pigeon_connector(self):
        klass = self.get_pigeon_connector_class()
        if not klass:
            raise ValueError(f"{self.connection_type} has no pigeon class")

        return klass(**self.data)

    def get_pigeon_connector_class(self):
        from recurvedata.pigeon.connector import get_connector_class

        connection_type = self.PIGEON_TYPE_MAPPING.get(self.connection_type, self.connection_type)
        try:
            return get_connector_class(connection_type)
        except KeyError:
            pigeon_cls = self.PIGEON_TYPE_CLS_MAPPING[connection_type]
            __import__(pigeon_cls)
            return get_connector_class(connection_type)

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
    def user(self):
        # used in email load
        return self.data.get("user")

    @property
    def password(self):
        # used in email load
        return self.data.get("password")

    @classmethod
    def is_support_connection_type(cls, connection_type: str) -> bool:
        connection_type = cls.PIGEON_TYPE_MAPPING.get(connection_type, connection_type)
        return connection_type in cls.PIGEON_TYPE_CLS_MAPPING

    @property
    def recurve_connector(self):
        """
        和 pigeon connector 区分开
        :return:
        """
        recurve_cls = self.recurve_connector_cls
        if not recurve_cls:
            raise ValueError(f"Unknown connection type: {self.connection_type}")
        recurve_con = recurve_cls(self.extra)
        return recurve_con

    # todo: is_dbapi


def get_pigeon_connector(connection_type: str, data: dict):
    return DataSource(connection_type=connection_type, data=data).get_pigeon_connector()
