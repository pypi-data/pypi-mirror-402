import logging
from collections import OrderedDict

from recurvedata.pigeon.utils.keyed_tuple import KeyedTuple

logger = logging.getLogger(__name__)


def tuple_factory(colnames, row):
    """Returns each row as a tuple"""
    return row


def keyed_tuple_factory(colnames, row):
    return KeyedTuple(row, colnames)


def dict_factory(colnames, row):
    return dict(zip(colnames, row))


def ordered_dict_factory(colnames, row):
    return OrderedDict(zip(colnames, row))


def get_row_keys(row):
    if isinstance(row, dict):
        # created by dict_factory or ordered_dict_factory
        return list(row.keys())
    if hasattr(row, "_fields"):
        # created by keyed_tuple_factory
        return list(row._fields)
    else:
        # created by tuple_factory, which is not able to know the keys
        return None


def get_row_values(row):
    if isinstance(row, dict):
        # created by dict_factory or ordered_dict_factory
        return list(row.values())
    return list(row)
