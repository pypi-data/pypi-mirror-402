from functools import partial

from recurvedata.pigeon.connector._registry import get_connector_class


def new_azure_synapse_connector(connection=None, database=None):
    """
    only connection string accepted
    database switching between  azure data warehouses is not allowed.
    """
    from .azure_synapse import AzureSynapseConnector

    conf = connection.copy()
    if database:
        conf["database"] = database
    return AzureSynapseConnector(**conf)


def new_azure_blob_connector(
    conn_string: str = None,
    account_url: str = None,
    endpoint_suffix: str = "core.chinacloudapi.cn",
    account_name: str = None,
    sas_token: str = None,
    **kwargs,
):
    """only connection string accepted"""
    from .azure_blob import AzureBlobConnector

    return AzureBlobConnector(
        connection_string=conn_string,
        account_url=account_url,
        endpoint_suffix=endpoint_suffix,
        account_name=account_name,
        sas_token=sas_token,
        **kwargs,
    )


def new_mysql_connector(connection=None, database=None, **kwargs):
    """Factory function to create a new MySQLConnector.

    :param connection: the connection properties,
    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    from .mysql import MySQLConnector

    conf = connection.copy()
    return MySQLConnector(database=database, **conf)


def new_tidb_connector(connection=None, database=None):
    """Factory function to create a new TiDBConnector (MySQLConnector).

    Similar to new_mysql_connector, but with different default connection parameter.

    :param connection: the connection properties
    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    return new_mysql_connector(connection, database)


def new_starrocks_connector(connection=None, database=None):
    """Factory function to create a new StarRocksConnector.

    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    from .starrocks import StarRocksConnector

    return StarRocksConnector(database=database, **connection)


def new_hive_connector(connection=None, database=None, **kwargs):
    """Factory function to create a new HiveConnector.

    :param connection: the connection properties
    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    from .hive_impala import HiveConnector

    conf = connection.copy()
    return HiveConnector(database=database, **conf)


def new_impala_connector(connection=None, database=None, **kwargs):
    """Factory function to create a new ImpalaConnector.

    :param connection: the connection properties
    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    from .hive_impala import ImpalaConnector

    conf = connection.copy()
    return ImpalaConnector(database=database, **conf)


def new_webhdfs_connector(conf=None, **kwargs):
    from .hdfs import HDFSConnector

    conf = conf.copy()
    return HDFSConnector(**conf)


def new_redshift_connector(connection=None, database=None):
    """Factory function to create a new RedshiftConnector.

    :param connection: the connection properties
    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    from .redshift import RedshiftConnector

    conf = connection.copy()
    return RedshiftConnector(database=database, **conf)


def new_postgresql_connector(connection=None, database=None):
    """Factory function to create a new PostgresConnector.

    :param connection: the connection properties
    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    from .postgresql import PostgresConnector

    conf = connection.copy()
    if database is not None:
        conf["database"] = database
    return PostgresConnector(**conf)


def new_cassandra_connector(connection, database=None):
    """Factory function to create a new CassandraConnector

    :param connection: the connection properties
    :type connection: dict
    :param database: the optional database name
    :type database: str
    """
    from .cass import CassandraConnector

    return CassandraConnector(database=database, **connection)


def new_s3_connector(conf=None):
    from .awss3 import S3Connector

    conf = conf.copy()
    return S3Connector(**conf)


def new_elasticsearch_connector(conf=None):
    from .es import ElasticSearchConnector

    return ElasticSearchConnector(**conf)


def new_ftp_connector(conf=None):
    from .ftp import FtpConnector

    conf = (conf or {}).copy()
    return FtpConnector(**conf)


def new_sftp_connector(conf):
    from .sftp import SFtpConnector

    return SFtpConnector(**conf)


def new_mssql_connector(connection=None, database=None, is_azure=False):
    from .mssql import AzureSQLServerConnector, MSSQLConnector

    conf = connection.copy()
    if database:
        conf["database"] = database
    if is_azure:
        connector_cls = AzureSQLServerConnector
    else:
        connector_cls = MSSQLConnector
    return connector_cls(**conf)


def new_clickhouse_connector(connection=None, database=None, native=True):
    conf = connection.copy()
    if not native:
        from .clickhouse import ClickHouseConnector
    else:
        from .clickhouse_native import ClickHouseConnector
    return ClickHouseConnector(database=database, **conf)


def new_phoenix_connector(connection=None, **kwargs):
    from .hbase_phoenix import PhoenixConnector

    conf = connection.copy()
    return PhoenixConnector(**conf)


def new_mongodb_connector(connection=None, **kwargs):
    from .mongodb import MongoDBConnector

    conf = connection.copy()
    return MongoDBConnector(**conf)


def new_google_bigquery_connector(*args, **kwargs):
    from .google_bigquery import GoogleBigqueryConnector

    return GoogleBigqueryConnector(*args, **kwargs)


def new_feishu_connector(app_id=None, app_secret=None):
    from .feishu import FeishuBot

    conf = {}
    if app_id:
        conf["app_id"] = app_id
        conf["app_secret"] = app_secret
    return FeishuBot(**conf)


def new_owncloud_connector(url: str = None, user: str = None, password: str = None, **kwargs):
    from .owncloud import OwncloudConnector

    conf = {}
    if url and user and password:
        conf["url"] = url
        conf["user"] = user
        conf["password"] = password
        conf.update(kwargs)
    else:
        raise ValueError("You must provide owncloud URL, user and password.")
    return OwncloudConnector(**conf)


def new_sqlite_connector(in_memory: bool, max_memory_gb: int = 2, **kwargs):
    if not in_memory:
        raise ValueError("Currently only supports in-memory database.")
    from .sqlite import SQLiteMemoryDbConnector

    conf = {}
    conf.update(kwargs)
    return SQLiteMemoryDbConnector(max_memory_gb=max_memory_gb, **conf)


def new_doris_connector(connection=None, database=None):
    from .doris import DorisConnector

    conf = connection.copy()
    return DorisConnector(database=database, **conf)


_factory_registry = {
    "mysql": new_mysql_connector,
    "tidb": new_tidb_connector,
    "hive": new_hive_connector,
    "impala": new_impala_connector,
    "redshift": new_redshift_connector,
    "cassandra": new_cassandra_connector,
    "s3": new_s3_connector,
    "elasticsearch": new_elasticsearch_connector,
    "es": new_elasticsearch_connector,
    "ftp": new_ftp_connector,
    "azure_synapse": new_azure_synapse_connector,
    "azure_blob": new_azure_blob_connector,
    "mssql": new_mssql_connector,
    "clickhouse": new_clickhouse_connector,
    "clickhouse_native": partial(new_clickhouse_connector, native=True),
    "phoenix": new_phoenix_connector,
    "mongodb": new_mongodb_connector,
    "gbq": new_google_bigquery_connector,
    "google_bigquery": new_google_bigquery_connector,
    "sqlite": new_sqlite_connector,
    "postgres": new_postgresql_connector,
    "doris": new_doris_connector,
    "starrocks": new_starrocks_connector,
}


def get_connector(db_type, *args, **kwargs):
    return _factory_registry[db_type](*args, **kwargs)
