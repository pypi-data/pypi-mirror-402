from recurvedata.pigeon.connector import get_connector
from recurvedata.pigeon.handler.csv_handler import CSVFileHandler, create_csv_file_handler_factory


def new_to_csv_dumper(
    dbtype, connection=None, database=None, connector=None, filename=None, transformer=None, hive=False, **dumper_kwargs
):
    if connector is None:
        connector = get_connector(dbtype, connection=connection, database=database)

    handler_factory_params = ["merge_files", "encoding", "write_header"] + CSVFileHandler.ERROR_HANDLE_PARAMS
    factory_options = dict(filename=filename, hive=hive, transformer=transformer)
    for p in handler_factory_params:
        if p in dumper_kwargs:
            factory_options[p] = dumper_kwargs.pop(p)
    factory = create_csv_file_handler_factory(**factory_options)
    dumper_kwargs.setdefault("handler_factories", [factory])

    row_factory = dumper_kwargs.pop("row_factory", None)

    if dbtype == "cassandra":
        from .cass import CassandraDumper

        dumper = CassandraDumper(connector, **dumper_kwargs)
    else:
        from .dbapi import DBAPIDumper

        dumper = DBAPIDumper(connector, **dumper_kwargs)

    if row_factory is not None:
        dumper.row_factory = row_factory

    return dumper


def new_tidb_to_csv_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("tidb", connection, database, filename, transformer, hive=False, **dumper_kwargs)


def new_tidb_to_hive_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("tidb", connection, database, filename, transformer, hive=True, **dumper_kwargs)


def new_mysql_to_csv_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("mysql", connection, database, filename, transformer, hive=False, **dumper_kwargs)


def new_mysql_to_hive_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("mysql", connection, database, filename, transformer, hive=True, **dumper_kwargs)


def new_redshift_to_csv_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("redshift", connection, database, filename, transformer, hive=False, **dumper_kwargs)


def new_redshift_to_hive_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("redshift", connection, database, filename, transformer, hive=True, **dumper_kwargs)


def new_impala_to_csv_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("impala", connection, database, filename, transformer, hive=False, **dumper_kwargs)


def new_impala_to_hive_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("impala", connection, database, filename, transformer, hive=True, **dumper_kwargs)


def new_phoenix_to_csv_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("phoenix", connection, database, filename, transformer, hive=False, **dumper_kwargs)


def new_phoenix_to_hive_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("phoenix", connection, database, filename, transformer, hive=True, **dumper_kwargs)


def new_clickhouse_to_csv_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("clickhouse", connection, database, filename, transformer, hive=False, **dumper_kwargs)


def new_clickhouse_to_hive_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("clickhouse", connection, database, filename, transformer, hive=True, **dumper_kwargs)


def new_cassandra_to_csv_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("cassandra", connection, database, filename, transformer, hive=False, **dumper_kwargs)


def new_cassandra_to_hive_dumper(connection=None, database=None, filename=None, transformer=None, **dumper_kwargs):
    return new_to_csv_dumper("cassandra", connection, database, filename, transformer, hive=True, **dumper_kwargs)


def new_elasticsearch_to_csv_dumper(hosts=None, filename=None, transformer=None, **dumper_kwargs):
    from recurvedata.pigeon.dumper.es import ElasticSearchDumper

    factory = create_csv_file_handler_factory(filename=filename, transformer=transformer)
    dumper_kwargs.setdefault("handler_factories", [factory])
    dumper = ElasticSearchDumper(connector=get_connector("es", host=hosts), **dumper_kwargs)
    return dumper


def new_elasticsearch_to_hive_dumper(hosts=None, filename=None, transformer=None, **dumper_kwargs):
    from recurvedata.pigeon.dumper.es import ElasticSearchDumper

    factory = create_csv_file_handler_factory(filename=filename, transformer=transformer, hive=True)
    dumper_kwargs.setdefault("handler_factories", [factory])
    dumper = ElasticSearchDumper(connector=get_connector("es", host=hosts), **dumper_kwargs)
    return dumper


def new_ftp_dumper(conf=None, **dumper_kwargs):
    from recurvedata.pigeon.dumper.ftp import FtpDumper

    dumper = FtpDumper(connector=get_connector("ftp", conf=conf), **dumper_kwargs)
    return dumper


def new_mongodb_to_csv_dumper(connection=None, filename=None, transformer=None, **dumper_kwargs):
    from recurvedata.pigeon.dumper.mongodb import MongoDBDumper

    factory = create_csv_file_handler_factory(filename=filename, transformer=transformer)
    dumper_kwargs.setdefault("handler_factories", [factory])
    dumper = MongoDBDumper(connector=get_connector("mongodb", connection=connection), **dumper_kwargs)
    return dumper


def new_mongodb_to_hive_dumper(connection=None, filename=None, transformer=None, **dumper_kwargs):
    from recurvedata.pigeon.dumper.mongodb import MongoDBDumper

    factory = create_csv_file_handler_factory(filename=filename, transformer=transformer, hive=True)
    dumper_kwargs.setdefault("handler_factories", [factory])
    dumper = MongoDBDumper(connector=get_connector("mongodb", connection=connection), **dumper_kwargs)
    return dumper


def new_google_bigquery_to_csv_dumper(
    filename=None,
    transformer=None,
    key_path=None,
    key_dict=None,
    proxies=None,
    location=None,
    hive=False,
    **dumper_kwargs,
):
    from recurvedata.pigeon.connector import new_google_bigquery_connector
    from recurvedata.pigeon.dumper.dbapi import DBAPIDumper

    connector = new_google_bigquery_connector(key_path=key_path, key_dict=key_dict, proxies=proxies, location=location)
    factory = create_csv_file_handler_factory(filename=filename, transformer=transformer, hive=hive, encoding="utf-8")
    dumper_kwargs.setdefault("handler_factories", [factory])
    dumper = DBAPIDumper(connector, **dumper_kwargs)
    row_factory = dumper_kwargs.pop("row_factory", None)
    if row_factory is not None:
        dumper.row_factory = row_factory
    return dumper


def new_clickhouse_native_to_csv_dumper(
    connection=None, database=None, filename=None, transformer=None, **dumper_kwargs
):
    return new_to_csv_dumper(
        "clickhouse_native", connection, database, filename, transformer, hive=False, **dumper_kwargs
    )


def new_clickhouse_native_to_hive_dumper(
    connection=None, database=None, filename=None, transformer=None, **dumper_kwargs
):
    return new_to_csv_dumper(
        "clickhouse_native", connection, database, filename, transformer, hive=True, **dumper_kwargs
    )
