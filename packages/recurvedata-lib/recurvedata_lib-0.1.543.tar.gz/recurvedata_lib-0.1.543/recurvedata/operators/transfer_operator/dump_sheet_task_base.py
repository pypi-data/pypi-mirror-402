import inspect
import json
import logging
import os

import jsonschema

from recurvedata.pigeon.handler.csv_handler import CSVFileHandler
from recurvedata.pigeon.utils import ensure_str_list, fs

try:
    import numpy as np
    import pandas as pd
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import DumpTask
from recurvedata.operators.utils import infer_schema_from_dataframe, parse_to_date
from recurvedata.utils.attrdict import AttrDict

logger = logging.getLogger(__name__)
_transform_default_value = """\
import pandas as pd


def transform(df: pd.DataFrame) -> pd.DataFrame:
    return df
"""


class SheetDumpTaskBase(DumpTask):
    _AUTO_REGISTER = False

    common_config_schema_properties = {
        "extra_read_kwargs": {
            "type": "string",
            "title": _l("Additional Read Parameters"),
            "description": _l(
                "Additional parameters to pass to pandas read_csv or read_excel functions in JSON format"
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "code",
                "lang": "json",
            },
        },
        "type_mapping": {
            "type": "string",
            "title": _l("Column Type Mapping"),
            "description": _l(
                'Specify data types for columns using format {"column_name": "data_type"}. '
                "This mapping is passed to DataFrame.astype() - see "
                '<a target="_blank" href="https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.astype.html">'
                "pandas documentation</a> for supported types."
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "code",
                "lang": "json",
            },
        },
        "date_columns": {
            "type": "string",
            "title": _l("Date Format Columns"),
            "description": _l("Comma-separated list of column names to parse as dates"),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
        "fillna_to_null": {
            "type": "boolean",
            "title": _l("Convert NaN to NULL"),
            "default": True,
        },
        "order_by": {
            "type": "string",
            "title": _l("Sort Order"),
            "description": _l(
                "Comma-separated list of columns to sort rows by. Original order is preserved if not specified."
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
        "column_name_mapping": {
            "type": "string",
            "title": _l("Rename Columns"),
            "description": _l('Map old column names to new names using format {"old_name": "new_name"}'),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "code",
                "lang": "json",
            },
        },
        "result_columns": {
            "type": "string",
            "title": _l("Output Columns"),
            "description": _l(
                "Comma-separated list of columns to include in output and their order. All columns included if not specified."
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
        "primary_keys": {
            "type": "string",
            "title": _l("Unique Key Columns"),
            "description": _l(
                "Comma-separated list of columns that should contain unique values. "
                "Task will fail if duplicates are found. Leave empty to skip uniqueness check."
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
        "not_nullable_columns": {
            "type": "string",
            "title": _l("Required Columns"),
            "description": _l(
                "Comma-separated list of columns that must not contain NULL values. "
                "Task will fail if NULL values are found in these columns."
            ),
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "plain",
            },
        },
        "transform_func": {
            "type": "string",
            "title": _l("Custom Transform"),
            "description": _l(
                "Optional Python function to transform the DataFrame. Must accept and return a pandas DataFrame. "
                "This transformation is applied after all other processing steps."
            ),
            "default": _transform_default_value,
            "ui:field": "CodeEditorWithReferencesField",
            "ui:options": {
                "type": "code",
                "lang": "python",
            },
        },
    }

    custom_config_schema_properties = {}

    custom_config_schema_required = []

    @classmethod
    def config_schema(cls):
        schema = {
            "type": "object",
            "properties": {},
            "required": cls.custom_config_schema_required,
        }
        schema["properties"].update(cls.custom_config_schema_properties)
        for k, v in cls.common_config_schema_properties.items():
            if k not in schema["properties"]:
                schema["properties"][k] = v
        return schema

    def execute_impl(self, *args, **kwargs):
        conf = self.rendered_config
        df = self.read_origin_df()

        df = self.apply_builtin_transform(conf, df)
        df = self.apply_validations(conf, df)
        df = self.apply_custom_transform_func(conf, df)

        self.df_to_csv(df)

    def read_origin_df(self) -> "pd.DataFrame":
        raise NotImplementedError

    def df_to_csv(self, df):
        logger.info(f"result DataFrame shape {df.shape}, dtypes:\n{df.dtypes}")
        logger.info(df.head())

        handler: CSVFileHandler = self.create_handler_factory().create_handler()
        for row in df.itertuples(index=False):
            handler.handle(row)
        handler.close()
        if handler.filename != self.filename and os.path.exists(handler.filename):
            os.rename(handler.filename, self.filename)
        logger.info(f"exported {len(df)} rows into {self.filename}")

        schema = infer_schema_from_dataframe(df)
        schema_filename = fs.schema_filename(self.filename)
        schema.dump(schema_filename)
        logger.info(f"saving schema to {schema_filename}")

    @staticmethod
    def apply_builtin_transform(conf: AttrDict, df: "pd.DataFrame") -> "pd.DataFrame":
        logger.info("apply_builtin_transform...")
        if conf.type_mapping:
            logger.info(f"  * convert dtypes with {conf.type_mapping}")
            df = df.astype(json.loads(conf.type_mapping))

        if conf.date_columns:
            cols = ensure_str_list(conf.date_columns)
            logger.info(f"  * parse {cols} to date")
            for col in cols:
                df[col] = df[col].map(parse_to_date)

        if conf.fillna_to_null:
            logger.info("  * fillna with None")
            df = df.fillna(np.nan).replace([np.nan], [None])

        if conf.order_by:
            cols = ensure_str_list(conf.order_by)
            logger.info("  * sort by {cols")
            df = df.sort_values(by=cols)

        if conf.column_name_mapping:
            logger.info(f"  * apply column name mapping {conf.column_name_mapping}")
            df = df.rename(json.loads(conf.column_name_mapping), axis=1)

        if conf.result_columns:
            cols = ensure_str_list(conf.result_columns)
            logger.info(f"  * change result columns with {cols}")
            df = df[cols]

        return df

    @staticmethod
    def apply_validations(conf: AttrDict, df: "pd.DataFrame") -> "pd.DataFrame":
        logger.info("apply_validations...")
        if conf.primary_keys:
            logger.info("  * checking duplication...")
            duplicate = df[df.duplicated(subset=ensure_str_list(conf.primary_keys))]
            if not duplicate.empty:
                logger.error(f"duplicate rows: {duplicate}")
                raise ValueError("duplication detected")

        if conf.not_nullable_columns:
            cols = ensure_str_list(conf.not_nullable_columns)
            logger.info(f"  * checking null to columns {cols}...")
            null_cols = []
            for col in cols:
                if df[col].isnull().values.any():
                    null_cols.append(col)
            if null_cols:
                logger.error(f"{null_cols} contains null values")
                raise ValueError(f"{null_cols} contains null values")

        return df

    @staticmethod
    def apply_custom_transform_func(conf: AttrDict, df: "pd.DataFrame") -> "pd.DataFrame":
        if not conf.transform_func:
            return df
        func = validate_transform(conf.transform_func)
        if not func:
            return df

        logger.info("apply transform function...")
        df = func(df)
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"transform function must return an Pandas DataFrame object, got {type(df)} instead")
        return df

    @classmethod
    def validate(cls, configuration):
        conf = super().validate(configuration)

        transform_func_code = conf.get("transform_func", "").strip()
        if transform_func_code:
            validate_transform(transform_func_code)
        return conf


def validate_transform(raw_code):
    code = compile(raw_code, "", "exec")
    ns = {}
    exec(code, ns)
    func = ns.get("transform")
    if not func:
        return None

    if not callable(func):
        raise jsonschema.ValidationError(message="transform should be callable", path=("transform_func",))

    sig = inspect.signature(func)
    if tuple(sig.parameters.keys()) != ("df",):
        raise jsonschema.ValidationError(
            message="transform must accept and only accept df as parameter", path=("transform_func",)
        )
    return func
