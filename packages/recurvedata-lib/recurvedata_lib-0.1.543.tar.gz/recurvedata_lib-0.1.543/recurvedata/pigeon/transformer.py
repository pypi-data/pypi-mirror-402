import struct
import zlib
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    # use ujson for better performance
    import ujson as json
except ImportError:
    import json

from recurvedata.pigeon import const
from recurvedata.pigeon.schema import Schema

_Row = Union[Tuple, Dict[str, Any]]


class Transformer:
    _input_schema: Optional[Schema] = None
    _use_input_schema_as_output: bool = False

    @property
    def input_schema(self) -> Optional[Schema]:
        """Returns the schema of input data"""
        return self._input_schema

    @input_schema.setter
    def input_schema(self, schema: Schema):
        """Should be called by the handler"""
        assert isinstance(schema, Schema)
        self._input_schema = schema

    @property
    def output_schema(self) -> Optional[Schema]:
        """Subclasses that change the rows schema should provide the output schema.

        These operations will change the output schema:
        - Add or remove fields
        - Change the name of fields
        - Change the type of fields

        An example of valid schema:

        from recurvedata.pigeon.schema import Schema, Field, types

        Schema([
            Field(name='id', type=types.INT32),
            Field(name='name', type=types.STRING, size=64),
            Field(name='snapshot_time', type=types.DATETIME, comment='snapshot_time in UTC'),
            Field(name='is_active', type=types.BOOLEAN)
        ])

        Allowed types:

        - INT8 = 'INT8'  # 1-byte (8-bit) signed integers
        - INT16 = 'INT16'  # 2-byte (16-bit) signed integers
        - INT32 = 'INT32'  # 4-byte (32-bit) signed integers
        - INT64 = 'INT64'  # 8-byte (64-bit) signed integers
        - FLOAT32 = 'FLOAT32'  # 4-byte (32-bit) single-precision floating
        - FLOAT64 = 'FLOAT64'  # 8-byte (64-bit) double-precision floating
        - BOOLEAN = 'BOOLEAN'
        - DATETIME = 'DATETIME'
        - DATE = 'DATE'
        - STRING = 'STRING'
        """
        if self._use_input_schema_as_output:
            return self._input_schema
        return None

    def transform(self, row: _Row, *args, **kwargs) -> Union[_Row, List[_Row]]:
        """This is the method called by Handler.

        It internally calls `transform_impl` to do the real transform logic.
        Subclasses should implement `transform_impl` but not this method.

        :param row: a Row (namedtuple) object contains a row record fetched from database
        :returns: returns one (tuple) or multiple (list of tuple) rows
        """
        return self.transform_impl(row, *args, **kwargs)

    def transform_impl(self, row: _Row, *args, **kwargs) -> Union[_Row, List[_Row]]:
        return row

    @staticmethod
    def convert_json_to_hive_map(data: Union[str, bytes]) -> str:
        if not data:
            return const.HIVE_NULL

        d = json.loads(data)
        items = []
        for key, value in d.items():
            key = str(key).strip()
            value = str(value).strip()
            item = '{0}{1}{2}'.format(key, const.HIVE_MAP_KV_DELIMITER, value)
            items.append(item)
        return const.HIVE_MAP_ITEM_DELIMITER.join(items)

    @staticmethod
    def convert_json_to_hive_array(data: Union[str, bytes]) -> str:
        if not data:
            return const.HIVE_NULL

        items = json.loads(data)
        return const.HIVE_ARRAY_DELIMITER.join(items)

    @staticmethod
    def mysql_uncompress(value: bytes, return_str: bool = False) -> Union[bytes, str]:
        """A Python implementation of UNCOMPRESS function of MySQL.

        Used to decompress result of COMPRESS function.

        https://dev.mysql.com/doc/refman/5.7/en/encryption-functions.html#function_compress

        :param value: the compressed data in bytes
        :param return_str: the return value should be unicode
        :type return_str: bool
        :rtype: bytes | str
        """

        # Empty strings are stored as empty strings.
        # Nonempty strings are stored as a 4-byte length of the uncompressed string
        if not value or len(value) < 4:
            return value

        rv = zlib.decompress(value[4:])

        if return_str:
            rv = rv.decode()
        return rv

    @staticmethod
    def mysql_compress(value: Optional[str]) -> Optional[bytes]:
        if value is None:
            return None
        if value == '':
            return b''
        size = struct.pack('I', len(value))
        data = zlib.compress(value.encode())
        return size + data

    @staticmethod
    def json_loads(*args, **kwargs) -> Any:
        return json.loads(*args, **kwargs)

    @staticmethod
    def json_dumps(*args, **kwargs) -> str:
        return json.dumps(*args, **kwargs)
