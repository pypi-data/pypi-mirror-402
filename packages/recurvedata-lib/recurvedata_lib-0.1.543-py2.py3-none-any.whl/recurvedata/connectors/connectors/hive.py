from dataclasses import dataclass
from typing import Optional, Type

from sqlalchemy.engine.url import URL

from recurvedata.connectors import get_connection_class
from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.connectors.mysql import CONNECTION_TYPE as MYSQL_CONNECTION_TYPE
from recurvedata.connectors.connectors.postgres import CONNECTION_TYPE as POSTGRES_CONNECTION_TYPE
from recurvedata.connectors.dbapi import DBAPIBase
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

HIVE_FIELD_DELIMITER = chr(1)
HIVE_ARRAY_DELIMITER = chr(2)
HIVE_MAP_ITEM_DELIMITER = chr(2)
HIVE_MAP_KV_DELIMITER = chr(3)
HIVE_NULL = r"\N"

CONNECTION_TYPE = "hive"
UI_CONNECTION_TYPE = "Apache Hive"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class HiveConnector(DBAPIBase):
    SYSTEM_DATABASES = [
        "information_schema",
    ]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = ["PyHive", "thrift-sasl"]
    driver = "hive"
    valid_metastore_types = [
        MYSQL_CONNECTION_TYPE,
        POSTGRES_CONNECTION_TYPE,
    ]
    category = [ConnectionCategory.WAREHOUSE]
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "title": _l("Host Address"),
                "default": "127.0.0.1",
            },
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 10000,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
                "default": "default",
            },
            "hdfs_options": {
                "type": "object",
                "title": _l("HDFS Options"),
                "description": _l("Configuration options for HDFS connection"),
                "properties": {
                    "host": {
                        "type": "string",
                        "title": _l("Host Address"),
                        "description": _l("HDFS namenode hostname or IP address"),
                    },
                    "port": {
                        "type": "number",
                        "title": _l("Port Number"),
                        "description": _l("HDFS namenode port number"),
                        "default": 50070,
                    },
                    "user": {"type": "string", "title": _l("Username")},
                    "staging_folder": {
                        "type": "string",
                        "title": _l("Transfer Staging Folder"),
                        "description": _l("Temporary HDFS directory path for data transfer staging"),
                        "default": "/tmp/recurve",
                    },
                },
                "order": ["host", "port", "user", "staging_folder"],
            },
            "auth": {
                "type": "string",
                "title": _l("Authentication Type"),
                "default": "LDAP",
            },
            "hive_conf": {
                "type": "object",
                "title": _l("Hive Execute Configurations"),
                "description": _l("Additional Hive execution parameters"),
                "properties": {
                    "spark.yarn.queue": {
                        "type": "string",
                        "title": _l("Hive On Spark Queue"),
                        "description": _l("YARN queue name for Spark execution"),
                    },
                    "tez.queue.name": {
                        "type": "string",
                        "title": _l("Hive On Tez Queue"),
                        "description": _l("YARN queue name for Tez execution"),
                    },
                },
                "order": ["spark.yarn.queue", "tez.queue.name"],
            },
            # 'metastore': {
            #     'title': 'Hive Metastore Config',
            #     'type': 'object',
            #     'properties': {
            #         'type': {
            #             'type': 'string',
            #             'title': 'Metastore Type',
            #             'default': MYSQL_CONNECTION_TYPE,
            #         },
            #         'host': {
            #             'type': 'string',
            #             'title': 'Metastore Host Address',
            #         },
            #         'user': {
            #             'type': 'string',
            #             'title': 'Metastore User Name',
            #         },
            #         'password': {
            #             'type': 'string',
            #             'title': 'Metastore Password',
            #         },
            #         'database': {
            #             'type': 'string',
            #             'title': 'Metastore Database Name',
            #         },
            #         'port': {
            #             'type': 'number',
            #             'title': 'Metastore Port Number',
            #         },
            #     },
            #     "order": ['host', 'port', 'user', 'password', 'database'],
            #     'secret': ['password'],
            # },
            # 'ssh_tunnel': SSH_TUNNEL_CONFIG_SCHEMA,
        },
        "order": [
            "host",
            "port",
            "user",
            "password",
            "database",
            "hdfs_options",
            "auth",
            "hive_conf",
        ],
        "required": ["host", "port"],
        "secret": ["password"],
    }

    @property
    def connect_args(self):
        return {"auth": "LDAP"}  # todo

    # generate_ddl todo: stored as parquet

    def _extract_column_name(self, column_type):
        visit_type = column_type.__visit_name__
        if visit_type == "type_decorator":
            return column_type.impl.__visit_name__
        return visit_type

    @property
    def metastore_connector(self) -> Optional[DBAPIBase]:
        if not self.metastore:
            return None
        metastore_config = MetastoreConfig(**self.metastore)
        return metastore_config.get_connector(self.conf.get("ssh_tunnel"))

    @property
    def sqlalchemy_url(self):
        host, port = self.host, self.port
        if self.ssh_tunnel and self.ssh_tunnel.is_active:
            host, port = self.ssh_tunnel.local_bind_host, self.ssh_tunnel.local_bind_port

        return URL(self.driver, self.user, self.password, host, port, self.database, query={"auth": self.auth})


@dataclass
class MetastoreConfig:
    type: str
    host: str
    user: str
    password: str
    database: str
    port: int

    def get_connector(self, ssh_tunnel_config: Optional[dict]) -> DBAPIBase:
        con_cls: Type[DBAPIBase] = get_connection_class(self.type)
        return con_cls(
            conf={
                "host": self.host,
                "user": self.user,
                "password": self.password,
                "database": self.database,
                "port": self.port,
                "ssh_tunnel": ssh_tunnel_config,
            }
        )
