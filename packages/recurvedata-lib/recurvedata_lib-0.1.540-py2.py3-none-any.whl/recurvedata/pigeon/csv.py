import contextlib
import csv
import logging
import sys

import cytoolz as toolz

from recurvedata.utils.imports import MockModule

try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = MockModule("numpy")
    pd = MockModule("pandas")

from recurvedata.pigeon import const
from recurvedata.pigeon.schema import Schema, types

csv.field_size_limit(sys.maxsize)

dialect_terms = (
    "delimiter",
    "doublequote",
    "escapechar",
    "lineterminator",
    "quotechar",
    "quoting",
    "skipinitialspace",
    "strict",
)


class ExtendedSniffer(csv.Sniffer):
    def __init__(self):
        super().__init__()
        self.preferred = [",", "\t", ";", " ", ":", "|", const.HIVE_FIELD_DELIMITER]


def copy_dialect(name, source_dialect):
    return dict_to_dialect(dialect_to_dict(source_dialect), name)


def dialect_to_dict(dialect):
    return {name: getattr(dialect, name) for name in dialect_terms if hasattr(dialect, name)}


def dict_to_dialect(d, name=""):
    class dialect(csv.Dialect):
        _name = name

    for name in dialect_terms:
        if name in d:
            setattr(dialect, name, d[name])
    return dialect


def infer_header(path, nbytes=10000, encoding="utf-8"):
    with open(path, "rb") as f:
        sample = f.read(nbytes).decode(encoding, "replace")
    sniffer = ExtendedSniffer()
    try:
        return sniffer.has_header(sample)
    except csv.Error:
        return None


def sniff_dialect(path, nbytes=10000, encoding="utf-8"):
    with open(path, "rb") as f:
        sample = f.read(nbytes).decode(encoding, "replace")
    sniffer = ExtendedSniffer()
    try:
        dialect = sniffer.sniff(sample, delimiters=sniffer.preferred)
    except csv.Error as e:
        logging.warning("failed to sniff dialect, copy from csv.excel. error: %s", e)
        dialect = copy_dialect(name="excel_copy", source_dialect=csv.excel)

    crnl, nl = "\r\n", "\n"
    dialect.lineterminator = crnl if crnl in sample else nl
    return dialect


class CSV(object):
    """
    Proxy for a CSV file.
    """

    def __init__(self, path, has_header=None, encoding="utf-8", **dialect_kwargs):
        self.path = path
        self._has_header = has_header
        self.encoding = encoding or "utf-8"
        self._dialect_kwargs = dialect_kwargs

    @toolz.memoize
    def _sniff_dialect(self):
        dialect = sniff_dialect(self.path, encoding=self.encoding)
        for k, v in self._dialect_kwargs.items():
            if k in dialect_terms:
                setattr(dialect, k, v)
        return dialect

    @property
    def dialect(self):
        return self._sniff_dialect()

    @property
    def dialect_options(self):
        return dialect_to_dict(self.dialect)

    @property
    def has_header(self):
        if self._has_header is None:
            self._has_header = infer_header(self.path, encoding=self.encoding)

        return self._has_header

    @property
    def header(self):
        if not self.has_header:
            return None

        with open(self.path, encoding=self.encoding, newline="") as f:
            reader = csv.reader(f, **self.dialect_options)
            header = next(reader)
        return tuple(header)

    def to_df(self):
        return pd.read_csv(self.path, encoding=self.encoding, dialect=self.dialect)

    @contextlib.contextmanager
    def reader(self, as_dict=False):
        if as_dict and not self.header:
            raise ValueError("missing header")

        with open(self.path, encoding=self.encoding, newline="") as fd:
            if as_dict:
                reader = csv.DictReader(fd, **self.dialect_options)
            else:
                if self.has_header:
                    fd.readline()  # skip header
                reader = csv.reader(fd, **self.dialect_options)
            yield reader

    @toolz.memoize
    def infer_schema(self):
        if not self.has_header:
            return None

        mapping = {
            np.int8: types.INT8,
            np.int16: types.INT16,
            np.int32: types.INT32,
            np.int64: types.INT64,
            np.float16: types.FLOAT32,
            np.float32: types.FLOAT32,
            np.float64: types.FLOAT64,
            np.datetime64: types.DATETIME,
            np.object_: types.STRING,
            np.str_: types.STRING,
        }
        # np.bool removed since numpy 1.20 https://github.com/numpy/numpy/releases/tag/v1.20.0
        if np.__version__ < "1.20.0":
            mapping[np.bool] = types.BOOLEAN
        else:
            mapping[np.bool_] = types.BOOLEAN

        df = pd.read_csv(self.path, encoding=self.encoding, dialect=self.dialect, nrows=500)
        schema = Schema()
        for col in df.columns:
            canonical_type = mapping.get(df.dtypes[col].type, types.STRING)
            schema.add_field_by_attrs(col, canonical_type)
        return schema
