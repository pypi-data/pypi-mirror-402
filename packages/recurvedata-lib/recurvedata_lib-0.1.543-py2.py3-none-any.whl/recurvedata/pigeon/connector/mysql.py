import re

import cytoolz as toolz
import pymysql
import sqlalchemy
import sqlalchemy.engine.url
from pymysql.constants import FIELD_TYPE
from pymysql.converters import escape_string

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.dbapi import DBAPIConnector, _ShowTableLikeMixin
from recurvedata.pigeon.schema import types
from recurvedata.pigeon.utils import fs, safe_int

_mysql_type_to_canonical_type = {
    FIELD_TYPE.TINY: types.INT8,
    FIELD_TYPE.SHORT: types.INT16,
    FIELD_TYPE.LONG: types.INT32,
    FIELD_TYPE.LONGLONG: types.INT64,
    FIELD_TYPE.INT24: types.INT64,
    FIELD_TYPE.FLOAT: types.FLOAT32,
    FIELD_TYPE.DOUBLE: types.FLOAT64,
    FIELD_TYPE.DECIMAL: types.FLOAT64,
    FIELD_TYPE.NEWDECIMAL: types.FLOAT64,

    FIELD_TYPE.TIMESTAMP: types.DATETIME,
    FIELD_TYPE.DATETIME: types.DATETIME,
    FIELD_TYPE.DATE: types.DATE,

    # others: types.STRING
}

_canonical_type_to_mysql_type = {
    types.BOOLEAN: 'TINYINT',
    types.INT8: 'TINYINT',
    types.INT16: 'SMALLINT',
    types.INT32: 'INT',
    types.INT64: 'BIGINT',
    types.FLOAT32: 'FLOAT',
    types.FLOAT64: 'DOUBLE',

    types.DATE: 'DATE',
    types.DATETIME: 'DATETIME',

    types.STRING: 'TEXT',
    types.JSON: 'TEXT',
}


@register_connector_class(['mysql', 'tidb'])
class MySQLConnector(_ShowTableLikeMixin, DBAPIConnector):
    _sqla_driver = 'mysql+pymysql'
    _sqla_url_query = {'charset': 'utf8mb4'}
    _default_port = 3306

    def connect_impl(self, autocommit=False, *args, **kwargs):
        kwargs.setdefault('cursorclass', pymysql.cursors.SSCursor)
        return pymysql.connect(host=self.host,
                               port=self.port or 3306,
                               user=self.user,
                               password=self.password,
                               database=self.database,
                               charset='utf8mb4',
                               autocommit=autocommit,
                               *args, **kwargs)

    def _get_sqlalchemy_uri(self):
        url = sqlalchemy.engine.url.URL(drivername=self._sqla_driver, host=self.host, port=self.port,
                                        username=self.user, password=self.password,
                                        database=self.database or '',
                                        query=self._sqla_url_query)
        return url.__to_string__(hide_password=False)

    @classmethod
    def escape_string(cls, v):
        return escape_string(v)

    def load_csv(self, table, filename, columns=None, delimiter=',', quotechar='"',
                 lineterminator='\r\n', escapechar=None, skiprows=0, using_insert=False, **kwargs):
        table = self.quote_identifier(table)
        if using_insert:
            method = self.load_csv_by_inserting
        else:
            if self.is_tidb():
                method = self._load_csv_tidb
            else:
                method = self._load_csv_mysql
        return method(table, filename, columns,
                      delimiter, quotechar, lineterminator, escapechar,
                      skiprows=skiprows, **kwargs)

    def _load_csv_mysql(self, table, filename, columns=None, delimiter=',', quotechar='"',
                        lineterminator='\r\n', escapechar=None, skiprows=0, **kwargs):
        if columns:
            cols = '({})'.format(', '.join(columns))
        else:
            cols = ''

        escape = "ESCAPED BY '{}'".format(escape_string(escapechar)) if escapechar else ''
        lineterminator = escape_string(lineterminator)
        ignore_lines = f'IGNORE {skiprows} LINES' if skiprows else ''
        query = f'''
            LOAD DATA LOCAL INFILE '{filename}'
            INTO TABLE {table}
            FIELDS TERMINATED BY '{delimiter}' ENCLOSED BY '{quotechar}' {escape}
            LINES TERMINATED BY '{lineterminator}'
            {ignore_lines}
            {cols}
        '''.strip()

        self._log(query)
        with self.cursor(local_infile=True) as cursor:
            cursor.execute(query)

    def _load_csv_tidb(self, table, filename, columns=None, delimiter=',', quotechar='"',
                       lineterminator='\r\n', escapechar=None, skiprows=0, **kwargs):
        infile = filename
        if skiprows:
            infile = fs.skip_lines(filename, skiprows)
        self._load_csv_mysql(table, infile, columns,
                             delimiter, quotechar, lineterminator, escapechar,
                             skiprows=0, **kwargs)
        if infile != filename:
            fs.remove_files_safely(infile)

    def is_mysql(self):
        return True

    @toolz.memoize
    def is_tidb(self):
        with self.cursor() as cursor:
            try:
                cursor.execute('SELECT tidb_version()')
                cursor.fetchall()
                return True
            except Exception as e:
                return False

    @staticmethod
    def to_canonical_type(type_code, size):
        return _mysql_type_to_canonical_type.get(type_code, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type, size):
        if canonical_type == types.STRING:
            mysql_type = 'TEXT'
            size = safe_int(size)

            # utf8mb4 uses 4 bytes for one rune
            # 255 / 4 = 63
            if 0 < size < 63:
                mysql_type = 'VARCHAR(255)'
            # 65535 / 4 = 16383
            elif size >= 16383:
                # MEDIUMTEXT is enough
                mysql_type = 'MEDIUMTEXT'
        else:
            mysql_type = _canonical_type_to_mysql_type.get(canonical_type, 'TEXT')
        return mysql_type

    def generate_ddl(self, table, database=None, if_exists=True):
        if database is None:
            database = self.database
        if not self.has_table(table, database):
            raise ValueError(f'Table {table!r} not exists in {database!r}')

        with self.cursor() as cursor:
            cursor.execute(f'USE {self.quote_identifier(database)}')
            cursor.execute(f'SHOW CREATE TABLE {self.quote_identifier(table)}')
            if_exists_stmt = ' IF NOT EXISTS ' if if_exists else ' '
            body = re.search(r'CREATE TABLE (.*)', cursor.fetchall()[0][1], flags=re.S).group(1)
            return f'CREATE TABLE{if_exists_stmt}{body}'


TiDBConnector = MySQLConnector
