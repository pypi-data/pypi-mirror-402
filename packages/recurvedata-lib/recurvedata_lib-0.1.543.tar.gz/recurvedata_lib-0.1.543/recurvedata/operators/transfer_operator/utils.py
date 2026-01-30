import importlib.util
import sys

from recurvedata.core.transformer import Transformer
from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const

allowed_modes = (const.LOAD_OVERWRITE, const.LOAD_MERGE, const.LOAD_APPEND)

_TRANSFORM_SKELETON = """\
from recurvedata.core.transformer import Transformer


class MyTransformer(Transformer):
    def transform_impl(self, row, *args, **kwargs):
        # The row is an OrderedDict. Write your custom transformation logic here.
        return row


# Instantiate the transformer, the name must be `transformer`
transformer = MyTransformer()
"""


TRANSFORM = {
    "type": "string",
    "title": _l("Custom Transformation"),
    "description": _l(
        "Python code to transform data during transfer. Must implement a Transformer class with "
        "transform_impl method that processes each row. See example code below."
    ),
    "default": _TRANSFORM_SKELETON,
    "ui:field": "CodeEditorWithReferencesField",
    "ui:options": {
        "type": "code",
        "lang": "python",
    },
}

LOAD_COMMON = {
    "mode": {
        "type": "string",
        "title": _l("Load Mode"),
        "description": _l("How to handle existing data in the target table"),
        "enum": list(allowed_modes),
        "enumNames": list(allowed_modes),
        "default": const.LOAD_OVERWRITE,
    },
    "primary_keys": {
        "type": "string",
        "title": _l("Primary Keys"),
        "description": _l(
            "Comma-separated list of columns used for deduplication in MERGE mode. "
            "Should be primary or unique key columns."
        ),
        "ui:field": "CodeEditorWithReferencesField",
        "ui:options": {
            "type": "plain",
        },
        "ui:hidden": '{{parentFormData.mode !== "MERGE"}}',
    },
    "dedup": {
        "type": "boolean",
        "title": _l("Enable Deduplication"),
        "default": False,
        "description": _l("Remove duplicate rows from the data before loading"),
        "ui:widget": "BaseCheckbox",
        "ui:options": {
            "label": _l("Enable Deduplication"),
        },
    },
    "dedup_uniq_keys": {
        "type": "string",
        "title": _l("Deduplication Keys"),
        "description": _l("Comma-separated list of columns that uniquely identify each row"),
        "ui:field": "CodeEditorWithReferencesField",
        "ui:options": {
            "type": "plain",
        },
        "ui:hidden": "{{!parentFormData.dedup}}",
    },
    "dedup_orderby": {
        "type": "string",
        "title": _l("Sort Order"),
        "description": _l("Comma-separated list of columns to sort by before deduplication"),
        "ui:field": "CodeEditorWithReferencesField",
        "ui:options": {
            "type": "plain",
        },
        "ui:hidden": "{{!parentFormData.dedup}}",
    },
    # "pre_queries": {
    #     "type": "string",
    #     "title": "Queries Ran Before Loading",
    #     "description": '新数据导入前运行的 SQL，多条 SQL 用 `;` 分隔；支持传入变量，详见 <a target="_blank" href="https://bit.ly/2JMutjn">文档</a>',
    #     "ui:field": "CodeEditorWithReferencesField",
    #     "ui:options": {
    #         "type": "code",
    #         "lang": "sql",
    #         "sqlLang": "sql",
    #     },
    # },
    # "post_queries": {
    #     "type": "string",
    #     "title": "Queries Ran After Loading",
    #     "description": '新数据导入后运行的 SQL，多条 SQL 用 `;` 分隔；支持传入变量，详见 <a target="_blank" href="https://bit.ly/2JMutjn">文档</a>',
    #     "ui:field": "CodeEditorWithReferencesField",
    #     "ui:options": {
    #         "type": "code",
    #         "lang": "sql",
    #         "sqlLang": "sql",
    #     },
    # },
}

__spec = importlib.util.spec_from_loader("recurve_hack", None)
__recurve_hack = importlib.util.module_from_spec(__spec)
sys.modules["recurve_hack"] = __recurve_hack


def validate_transform(raw_code):
    from recurvedata.pigeon.transformer import Transformer as PigeonTransformer

    code = compile(raw_code, "", "exec")
    exec(code, __recurve_hack.__dict__)
    transformer = __recurve_hack.__dict__.get("transformer")
    if not transformer:
        raise ValueError("transformer is required")
    if (
        not isinstance(transformer, (Transformer, PigeonTransformer))
        and transformer.__class__.__name__ != "MyTransformer"
    ):
        raise TypeError(f"transformer should be type of pigeon.transformer.Transformer, {type(transformer)}")
    return transformer
