import sqlite3

import pandas as pd


class SQLiteMemoryDbConnector:
    """
    SQLite 内存数据库连接器，用于在内存中的pandas Dataframe执行SQL查询, 支持标准SQL语法
    暂时只支持内存数据库, 不连接实体表和库
    python进程关闭后，所有表和数据都会丢失
    e.g.
    sqlite_conn = SQLiteMemoryDbConnector()
    df_1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    df_2 = pd.DataFrame({'a': [4, 5, 6], 'b': [7, 8, 9]})
    sqlite_conn.create_temp_table(df_1, 'df_1')
    sqlite_conn.create_temp_table(df_2, 'df_2')
    result = sqlite_conn.get_pandas_df('SELECT *,row_number() over(partition by a order by b) as rn FROM df_1')
    """

    def __init__(self, max_memory_gb, **kwargs):
        self.conn = sqlite3.connect(database=':memory:', **kwargs)  # 创建内存中的 SQLite 数据库
        self.conn.execute(f"PRAGMA max_memory = {max_memory_gb * 1024 * 1024}")
        self.cursor = self.conn.cursor()
        self.loaded_tables = set()

    def create_temp_table(self, df, table_name):
        """ Write a table in the memory database. """
        df.to_sql(table_name, self.conn, index=False, if_exists='replace')

    def drop_temp_table(self, table_name):
        """ Drop a table in the memory database. """
        self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    def get_pandas_df(self, query: str) -> pd.DataFrame:
        """
        :param query: SQL 查询语句
        :return: pandas DataFrame
        """
        return pd.read_sql_query(query, self.conn)

    def close(self):
        self.conn.close()
