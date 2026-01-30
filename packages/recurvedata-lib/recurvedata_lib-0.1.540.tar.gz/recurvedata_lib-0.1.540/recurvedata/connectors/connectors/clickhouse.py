from typing import Any

from loguru import logger

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.datasource import DataSourceWrapper
from recurvedata.connectors.dbapi import DBAPIBase
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "clickhouse"
UI_CONNECTION_TYPE = "ClickHouse"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class ClickhouseConnector(DBAPIBase):
    SYSTEM_DATABASES = [
        "system",
        "information_schema",
    ]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = ["clickhouse-sqlalchemy"]
    driver = "clickhouse+native"
    group = [ConnectorGroup.DESTINATION]

    # Official ClickHouse data types from documentation
    available_column_types = [
        # Base types from DBAPIBase
        *DBAPIBase.available_column_types,
        # Integer types (official)
        "int8",
        "int16",
        "int32",
        "int64",
        "int128",
        "int256",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "uint128",
        "uint256",
        # Float types (official)
        "float32",
        "float64",
        "bfloat16",
        # String types (official)
        "string",
        "fixedstring",
        # Date/Time types (official)
        "date",
        "date32",
        "datetime",
        "datetime64",
        # Boolean type (official)
        "boolean",
        # UUID type (official)
        "uuid",
        # Network types (official)
        "ipv4",
        "ipv6",
        # Complex types (official)
        "array",
        "tuple",
        "map",
        "variant",
        # Enum types (official)
        "enum",
        "enum8",
        "enum16",
        # Wrapper types (official)
        "nullable",
        "lowcardinality",
        # Aggregate function types (official)
        "aggregatefunction",
        "simpleaggregatefunction",
        # Special types (official)
        "nested",
        "dynamic",
        "json",
        # Decimal type (official)
        "decimal",
        "decimal32",
        "decimal64",
        "decimal128",
        "decimal256",
    ]

    column_type_mapping = {
        "integer": [
            "Int8",
            "Int16",
            "Int32",
            "Int64",
            "Int128",
            "Int256",
            "UInt8",
            "UInt16",
            "UInt32",
            "UInt64",
            "UInt128",
            "UInt256",
        ],
        "string": ["String", "FixedString", "LowCardinality(String)"],
    }
    config_schema = {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "title": _l("Host Address"),
                "default": "127.0.0.1",
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
            },
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "description": _l(
                    "Native Protocol port number for the ClickHouse server connection. "
                    "Normally, default is 9000 for native protocol, use 9440 if secure SSL/TLS is enabled."
                ),
                "default": 9000,
            },
            "secure": {
                "type": "boolean",
                "title": _l("Use Secure Connection"),
                "description": _l("Enable secure SSL/TLS connection to ClickHouse"),
                "default": False,
            },
        },
        "order": ["host", "port", "user", "password", "database", "secure"],
        "required": [
            "host",
        ],
        "secret": ["password"],
    }

    def _extract_column_name(self, column_type):
        if column_type.__visit_name__ == "nullable":
            return column_type.nested_type.__visit_name__
        return column_type.__visit_name__

    def sqlalchemy_column_type_code_to_name(self, type_code: Any, size: int | None = None) -> str:
        """
        Convert SQLAlchemy cursor.description type_code to ClickHouse data type name.

        ClickHouse Connect uses string type names directly in cursor.description,
        so we can return the type_code as-is if it's a valid ClickHouse type,
        otherwise fall back to a default type.
        """
        if isinstance(type_code, str):
            # ClickHouse Connect returns string type names directly
            type_name = type_code.lower()

            # Check if it's a valid ClickHouse type
            if type_name in self.available_column_types:
                return type_name

            # Handle common type mappings for ClickHouse
            type_mapping = {
                # Common SQL type aliases to ClickHouse types
                "int": "int32",
                "integer": "int32",
                "bigint": "int64",
                "smallint": "int16",
                "tinyint": "int8",
                "double": "float64",
                "float": "float32",
                "real": "float32",
                "varchar": "string",
                "char": "string",
                "text": "string",
                "blob": "string",
                "timestamp": "datetime",
                "bool": "boolean",
                # ClickHouse specific mappings for edge cases
                "nothing": "string",  # Fallback for Nothing type
                "expression": "string",  # Fallback for Expression type
                "set": "string",  # Fallback for Set type
                "array(string)": "array",
                "array(date)": "array",
                "array(datetime)": "array",
                "array(float64)": "array",
                "array(float32)": "array",
                "array(int64)": "array",
                "array(int32)": "array",
            }

            mapped_type = type_mapping.get(type_name)
            if mapped_type and mapped_type in self.available_column_types:
                return mapped_type

        # For any other type_code format, try to convert to string and check again
        try:
            type_str = str(type_code).lower()
            if type_str in self.available_column_types:
                return type_str
        except (ValueError, TypeError):
            pass

        # Default fallback
        return "string"

    def convert_config_to_cube_config(
        self, database: str, schema: str = None, datasource: DataSourceWrapper = None
    ) -> dict:
        config = {
            "type": "clickhouse",
            "host": self.host,
            "user": datasource.user,
            "password": datasource.password,
            "database": database or self.database,
        }
        return config

    @classmethod
    def convert_normalized_type_to_db_type(cls, normalized_type: str) -> str:
        """
        Convert normalized type to ClickHouse data type name.
        Maps common normalized types to their preferred ClickHouse equivalents.
        """
        type_mapping = {
            "integer": "Int32",
            "float": "Float64",
            "string": "String",
            "boolean": "Boolean",
            "date": "Date",
            "datetime": "DateTime",
            "time": "DateTime",
            "binary": "String",
            "json": "String",
        }
        _type = type_mapping.get(normalized_type.lower())
        if not _type:
            logger.warning(f"Unsupported normalized type: {normalized_type}, using String as default")
            return "String"
        return _type
