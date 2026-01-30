import phoenixdb
from phoenixdb.cursor import Cursor

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.dbapi import DBAPIConnector
from recurvedata.pigeon.schema import types

# Phoenix Data Types: http://phoenix.apache.org/language/datatypes.html
_phoenix_type_to_canonical_type = {
    'INTEGER': types.INT32,
    'UNSIGNED_INT': types.INT32,
    'BIGINT': types.INT64,
    'UNSIGNED_LONG': types.INT64,
    'TINYINT': types.INT8,
    'UNSIGNED_TINYINT': types.INT8,
    'SMALLINT': types.INT16,
    'UNSIGNED_SMALLINT': types.INT16,
    'FLOAT': types.FLOAT32,
    'UNSIGNED_FLOAT': types.FLOAT32,
    'DOUBLE': types.FLOAT64,
    'UNSIGNED_DOUBLE': types.FLOAT64,
    'DECIMAL': types.FLOAT64,
    'BOOLEAN': types.BOOLEAN,

    'TIME': types.STRING,
    'UNSIGNED_TIME': types.STRING,
    'DATE': types.DATE,
    'UNSIGNED_DATE': types.DATE,
    'TIMESTAMP': types.DATETIME,
    'UNSIGNED_TIMESTAMP': types.DATETIME,

    'VARCHAR': types.STRING,
    'CHAR': types.STRING,

    # default: types.STRING
}

_canonical_type_to_phoenix_type = {
    types.BOOLEAN: 'BOOLEAN',
    types.INT8: 'TINYINT',
    types.INT16: 'SMALLINT',
    types.INT32: 'INTEGER',
    types.INT64: 'BIGINT',
    types.FLOAT32: 'FLOAT',
    types.FLOAT64: 'DOUBLE',

    types.DATE: 'DATE',
    types.DATETIME: 'DATETIME',

    types.STRING: 'VARCHAR',
    types.JSON: 'VARCHAR',
}


class PhoenixCursor(Cursor):
    itersize = 1000


@register_connector_class(['phoenix'])
class PhoenixConnector(DBAPIConnector):
    _default_port = 8765
    _identifier_start_quote = '"'
    _identifier_end_quote = '"'

    def connect_impl(self, autocommit=False, *args, **kwargs):
        url = f'http://{self.host}:{self.port}'
        return phoenixdb.connect(url=url, autocommit=autocommit, cursor_factory=PhoenixCursor, *args, **kwargs)

    def create_engine(self, engine_kwargs=None):
        raise NotImplementedError

    def has_table(self, table, database=None, **kwargs):
        if database is None:
            query = 'SELECT 1 FROM system.catalog WHERE table_name = ? LIMIT 1'
            params = [table]
        else:
            query = 'SELECT 1 FROM system.catalog WHERE table_name = ? AND table_schem = ? LIMIT 1'
            params = [table, database]
        return self.fetchone(query, params) is not None

    def get_columns(self, table, database=None, exclude=None):
        if database:
            clause = f'table_schem = {database!r}'
        else:
            clause = 'table_schem IS NULL'
        query = f'''
            SELECT column_name FROM system.catalog
            WHERE {clause} AND table_name = ? AND ordinal_position IS NOT NULL
            ORDER BY ordinal_position
        '''
        cols = [x[0] for x in self.fetchall(query, [table])]
        if not cols:
            raise ValueError('Table {!r} not exists in {!r}'.format(table, database))

        if exclude:
            cols = [x for x in cols if x not in exclude]
        return cols

    def is_phoenix(self):
        return True

    @staticmethod
    def to_canonical_type(type_code, size):
        return _phoenix_type_to_canonical_type.get(type_code, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type, size):
        return _canonical_type_to_phoenix_type.get(canonical_type, 'VARCHAR')
