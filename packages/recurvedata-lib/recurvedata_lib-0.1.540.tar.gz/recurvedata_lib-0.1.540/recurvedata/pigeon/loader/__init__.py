from recurvedata.pigeon.connector import (
    new_azure_synapse_connector,
    new_elasticsearch_connector,
    new_google_bigquery_connector,
    new_postgresql_connector,
    new_redshift_connector,
    new_tidb_connector,
)
from recurvedata.pigeon.loader.csv_to_azure_synapse import CSVToAzureSynapseLoader
from recurvedata.pigeon.loader.csv_to_clickhouse import CSVToClickHouseLoader
from recurvedata.pigeon.loader.csv_to_es import CSVToElasticSearchLoader
from recurvedata.pigeon.loader.csv_to_google_bigquery import CSVToGoogleBigqueryLoader
from recurvedata.pigeon.loader.csv_to_hive import CSVToHiveLoader
from recurvedata.pigeon.loader.csv_to_mysql import CSVToMySQLLoader
from recurvedata.pigeon.loader.csv_to_postgresql import CSVToPostgresqlLoader
from recurvedata.pigeon.loader.csv_to_redshift import CSVToRedshiftLoader
from recurvedata.pigeon.loader.csv_to_starrocks import CSVToStarRocksLoader


def new_csv_to_hive_loader(table, filename, database, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename, database=database)
    loader = CSVToHiveLoader(**params)
    return loader


def new_csv_to_mysql_loader(table, filename, database, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename, database=database)
    loader = CSVToMySQLLoader(**params)
    return loader


def new_csv_to_starrocks_loader(table, filename, database, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename, database=database)
    loader = CSVToStarRocksLoader(**params)
    return loader


def new_csv_to_tidb_loader(table, filename, database, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename, database=database)
    loader = CSVToMySQLLoader(**params)
    return loader


def new_csv_to_redshift_loader(table, filename, database, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename, database=database)
    loader = CSVToRedshiftLoader(**params)
    return loader


def new_csv_to_postgresql_loader(table, filename, database, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename, database=database)
    loader = CSVToPostgresqlLoader(**params)
    return loader


def new_csv_to_azure_synapse_loader(table, filename, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename)
    loader = CSVToAzureSynapseLoader(**params)
    return loader


def new_csv_to_clickhouse_loader(table, filename, database, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename, database=database)
    loader = CSVToClickHouseLoader(**params)
    return loader


def new_csv_to_elasticsearch_loader(index, filename, **kwargs):
    params = kwargs.copy()
    params.update(index=index, filename=filename)
    loader = CSVToElasticSearchLoader(**params)
    return loader


def new_csv_to_google_bigquery_loader(table, filename, **kwargs):
    params = kwargs.copy()
    params.update(table=table, filename=filename)
    loader = CSVToGoogleBigqueryLoader(**params)
    return loader
