"""
Azure Synapse Analytics（previous Azure SQL Data Warehouse）

doc：https://docs.microsoft.com/en-us/azure/synapse-analytics/sql-data-warehouse/sql-data-warehouse-overview-what-is
"""

import pandas as pd

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.mssql import AzureSQLServerConnector


@register_connector_class(["azure_synapse", "azure_dw"])
class AzureSynapseConnector(AzureSQLServerConnector):
    _autocommit = True

    def is_azure_synapse(self):
        return True

    def load_csv(
        self,
        table,
        filename,
        schema="dbo",
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        **kwargs,
    ):
        options = dict(
            columns=columns,
            delimiter=delimiter,
            quotechar=quotechar,
            lineterminator=lineterminator,
            escapechar=escapechar,
            skiprows=skiprows,
        )
        options.update(**kwargs)
        self.load_csv_bulk(table, filename, schema, **options)

    def get_pandas_df(self, query, parameters=None, **kwargs):
        # 没有 AUTOCOMMIT 的话， 会报错 An attempt to complete a transaction has failed. No corresponding transaction found.
        con = self.create_engine({"isolation_level": "AUTOCOMMIT"})
        try:
            df = pd.read_sql_query(sql=query, con=con, params=parameters, **kwargs)
        finally:
            con.dispose()
        return df
