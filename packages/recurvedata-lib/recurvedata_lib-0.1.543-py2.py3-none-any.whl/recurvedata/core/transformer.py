import json
import struct
import zlib
from typing import Literal

from recurvedata.pigeon.schema import Schema
from recurvedata.utils.crypto_util import CryptoUtil


class Transformer:
    @property
    def input_schema(self):
        """Returns the schema of input data"""
        return getattr(self, "_input_schema", None)

    @input_schema.setter
    def input_schema(self, schema):
        """Should be called by the handler"""
        assert isinstance(schema, Schema)
        setattr(self, "_input_schema", schema)

    @property
    def output_schema(self):
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
            Field(name='snapshot_time', type=types.DATETIME),
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
        return None

    def transform(self, row: dict, *args, **kwargs) -> dict | list[dict] | None:
        """This is the method called by Handler.

        It internally calls `transform_impl` to do the real transform logic.
        Subclasses should implement `transform_impl` but not this method.

        :param row: a Row (namedtuple) object contains a row record fetched from database
        :type row: collection.namedtuple
        :returns: returns one (tuple) or multiple (list of tuple) rows
        """
        return self.transform_impl(row, *args, **kwargs)

    def transform_impl(self, row: dict, *args, **kwargs) -> dict | list[dict] | None:
        """subclass should override this method to implement the custom transform operations"""
        return row

    @staticmethod
    def convert_json_to_hive_map(data: str | dict) -> str:
        from recurvedata.connectors.connectors.hive import (  # lazy import
            HIVE_MAP_ITEM_DELIMITER,
            HIVE_MAP_KV_DELIMITER,
            HIVE_NULL,
        )

        if not data:
            return HIVE_NULL

        if isinstance(data, str):
            d = json.loads(data)
        else:
            d = data

        items = []
        for key, value in d.items():
            key = str(key).strip()
            value = str(value).strip()
            item = f"{key}{HIVE_MAP_KV_DELIMITER}{value}"
            items.append(item)
        return HIVE_MAP_ITEM_DELIMITER.join(items)

    @staticmethod
    def convert_json_to_hive_array(data: str | list) -> str:
        from recurvedata.connectors.connectors.hive import HIVE_ARRAY_DELIMITER, HIVE_NULL

        if not data:
            return HIVE_NULL

        if isinstance(data, str):
            items = json.loads(data)
        else:
            items = data

        return HIVE_ARRAY_DELIMITER.join(items)

    @staticmethod
    def mysql_uncompress(value: bytes, return_str=False) -> str | bytes:
        """An Python implementation of UNCOMPRESS function of MySQL.

        Used to decompress result of COMPRESS function.

        https://dev.mysql.com/doc/refman/5.7/en/encryption-functions.html#function_compress

        :param value: the compressed data in bytes
        :type value: bytes
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
    def mysql_compress(value: str) -> bytes | None:
        if value is None:
            return None
        if value == "":
            return b""
        size = struct.pack("I", len(value))
        data = zlib.compress(value.encode())
        return size + data

    @staticmethod
    def json_loads(*args, **kwargs):
        return json.loads(*args, **kwargs)

    @staticmethod
    def json_dumps(*args, **kwargs) -> str:
        return json.dumps(*args, **kwargs)

    def aes_encrypt(
        self, key_name: str, data: str | bytes, mode: Literal["ECB", "CBC"] = "ECB", iv: str | bytes = None
    ) -> str:
        return CryptoUtil.base64_encode(CryptoUtil.aes_encrypt(key_name, data, mode, iv))

    def aes_decrypt(self, key_name: str, data: bytes | str) -> str:
        if isinstance(data, str):
            data = CryptoUtil.base64_decode(data)
        return CryptoUtil.aes_decrypt(key_name, data)

    def rsa_encrypt(self, key_name: str, data: str | bytes) -> str:
        return CryptoUtil.base64_encode(CryptoUtil.rsa_encrypt(key_name, data))

    def rsa_decrypt(self, key_name: str, data: bytes | str) -> str:
        if isinstance(data, str):
            data = CryptoUtil.base64_decode(data)
        return CryptoUtil.rsa_decrypt(key_name, data)

    def base64_encode(self, data: str | bytes) -> str:
        return CryptoUtil.base64_encode(data)

    def base64_decode(self, data: str | bytes) -> str:
        return CryptoUtil.base64_decode(data)

    def md5(self, data: str | bytes) -> str:
        return CryptoUtil.md5(data)

    def sha1(self, data: str | bytes) -> str:
        return CryptoUtil.sha1(data)

    def sha256(self, data: str | bytes) -> str:
        return CryptoUtil.sha256(data)
