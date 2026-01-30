import datetime
from typing import TYPE_CHECKING

import dateutil.parser

if TYPE_CHECKING:
    import pandas as pd


def parse_to_date(s: str) -> datetime.date:
    if isinstance(s, pd.Timestamp):
        return s.date()
    return dateutil.parser.parse(s).date()


def infer_schema_from_dataframe(df: "pd.DataFrame"):
    import numpy as np

    from recurvedata.pigeon.schema import Schema, types

    mapping = {
        np.bool: types.BOOLEAN,
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
        np.bool_: types.BOOLEAN,
    }

    schema = Schema()
    for col in df.columns:
        canonical_type = mapping.get(df.dtypes[col].type, types.STRING)
        schema.add_field_by_attrs(col, canonical_type)
    return schema


def once(func):
    def wrapper(*args, **kwargs):
        if not wrapper.called:
            wrapper.result = func(*args, **kwargs)
            wrapper.called = True
        return wrapper.result

    wrapper.called = False
    return wrapper
