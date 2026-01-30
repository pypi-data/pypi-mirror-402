from dataclasses import fields
from typing import Any

from recurvedata.utils.helpers import extract_dict


def init_dataclass_from_dict(dc_cls, arg_dct: dict[str, Any], **kwargs):
    field_names = [f.name for f in fields(dc_cls) if f.init]

    valid_arg_dct = extract_dict(arg_dct, field_names)
    return dc_cls(**valid_arg_dct, **kwargs)
