class ColumnTypeNormalizer:
    """
    A class to normalize database column types to a standard set of types.

    Attributes:
    - database (str): The name of the database for which normalization is needed.
    - _normalized_types (dict[str, list[str]]): A dictionary mapping normalized types to their corresponding database-specific types.

    Usage examples:
    >>> mysql_normalizer = ColumnTypeNormalizer(database='mysql')
    >>> mysql_normalizer.normalize('varchar')
    "string"
    >>> mysql_normalizer.normalize('tinyint(1)')
    "boolean"
    >>> postgres_normalizer = ColumnTypeNormalizer(database='postgresql')
    >>> postgres_normalizer.normalize('int4')
    "integer"
    >>> postgres_normalizer.normalize('jsonb')
    "json"
    >>> snowflake_normalizer = ColumnTypeNormalizer(database='snowflake')
    >>> snowflake_normalizer.normalize('timestamp_ntz')
    "datetime"
    >>> snowflake_normalizer.normalize('variant')
    "json"
    """

    _COMMON_NORMALIZED_TYPES: dict[str, list[str]] = {
        "integer": [
            "int",
            "integer",
            "smallint",
            "bigint",
            "tinyint",
            "int2",
            "int4",
            "int8",
            "int16",
            "int32",
            "int64",
        ],
        "float": ["float", "double", "real", "decimal", "numeric"],
        "string": ["varchar", "char", "text", "character varying", "nvarchar", "nchar", "clob", "string"],
        "boolean": ["bool", "boolean"],
        "date": ["date"],
        "datetime": ["datetime", "timestamp", "timestamp with time zone", "timestamp without time zone"],
        "time": ["time"],
        "binary": ["binary", "blob", "varbinary"],
        "json": ["json", "jsonb", "object", "variant", "array"],
    }

    def __init__(self, database: str, custom_mappings: dict[str, list[str]] | None = None):
        """
        Initializes the normalizer for a specific database with optional custom mappings.

        Args:
        - database: The name of the database for which normalization is needed.
        - custom_mappings: A dictionary mapping database-specific types to normalized types.
        """
        self.database = database.lower()
        # Convert common types and their mappings to lowercase
        self._normalized_types = {
            k.lower(): [v.lower() for v in values] for k, values in self._COMMON_NORMALIZED_TYPES.items()
        }

        # Convert custom mappings to lowercase, if provided
        if custom_mappings:
            for key, values in custom_mappings.items():
                key = key.lower()
                values = [v.lower() for v in values]
                if key in self._normalized_types:
                    self._normalized_types[key].extend(values)
                else:
                    self._normalized_types[key] = values

    def normalize(self, column_type: str) -> str:
        """
        Normalizes a given database column type to a standard type.

        Args:
        - column_type: The database column type to normalize.

        Returns:

        Usage example:
        >>> normalizer = ColumnTypeNormalizer('postgresql')
        >>> normalizer.normalize('int4')
        "integer"
        """
        column_type = column_type.lower()

        for normalized, column_types in self._normalized_types.items():
            for _type in column_types:
                if _type.startswith(column_type):
                    return normalized

        return column_type


if __name__ == "__main__":
    import doctest

    doctest.testmod()
