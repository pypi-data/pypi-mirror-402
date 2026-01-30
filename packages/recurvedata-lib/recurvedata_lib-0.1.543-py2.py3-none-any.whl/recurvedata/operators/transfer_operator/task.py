import json
import logging
import os
import shutil
import tempfile
import traceback

import jsonschema

from recurvedata.core.transformer import Transformer
from recurvedata.operators.task import BaseTask
from recurvedata.utils.attrdict import AttrDict
from recurvedata.utils.date_time import round_time_resolution
from recurvedata.utils.helpers import first
from recurvedata.utils.registry import Registry

try:
    from recurvedata.pigeon.handler.csv_handler import create_csv_file_handler_factory
    from recurvedata.pigeon.utils import fs, trim_suffix
except ImportError:
    pass

from recurvedata.operators.transfer_operator import utils

logger = logging.getLogger(__name__)
_registry = Registry(key_callback=lambda x: x.name())
_load_task_registry = Registry(key_callback=lambda x: x.ds_types)


class Task(BaseTask):
    worker_install_require = []
    web_install_require = []

    def __init__(self, dag, node, execution_date, variables, config, filename):
        super().__init__(dag, node, execution_date, variables)

        self.config = AttrDict(config)
        self.filename = filename

    @classmethod
    def type(cls):
        return None

    @staticmethod
    def first_or_default(dss, default=""):
        return first(dss, default)


class DumpTask(Task):
    _AUTO_REGISTER = True
    _MAX_ERROR_RATE = 0
    no_template_fields = (
        "data_source_name",
        "filter_engine",
    )

    @classmethod
    def type(cls):
        return "dump"

    @property
    def stage(self) -> str:
        return "dump"

    def __init_subclass__(cls, **kwargs):
        if cls._AUTO_REGISTER:
            _registry.add(cls)

    def __init__(self, handler_options=None, *args, **kwargs):
        self.handler_options = handler_options or {}
        super().__init__(*args, **kwargs)

    @classmethod
    def validate(cls, configuration):
        config = super().validate(configuration)

        transformer_code = configuration.get("transform", "").strip()
        if not transformer_code:
            return config
        try:
            utils.validate_transform(transformer_code)
        except (ValueError, TypeError) as e:
            raise jsonschema.ValidationError(message=str(e), path=("transform",))
        except Exception:
            tb = traceback.format_exc(limit=0)
            msg = "\n".join(tb.splitlines()[1:])
            raise jsonschema.ValidationError(message=msg, path=("transform",))

        if "custom_handler_options" in config:
            try:
                value = json.loads(config["custom_handler_options"])
            except Exception:
                raise jsonschema.ValidationError(
                    message="custom_handler_options should be valid JSON", path=("custom_handler_options",)
                )
            if not isinstance(value, dict):
                raise jsonschema.ValidationError(
                    message="custom_handler_options should be dict", path=("custom_handler_options",)
                )
        return config

    def create_handler_factory(self):
        self.remove_intermediate_files()
        transformer = self.create_transformer()
        kwargs = self.handler_options.copy()
        encoding = self.rendered_config.get("middle_file_encoding")
        kwargs.update(
            {
                "filename": self.filename,
                "encoding": encoding,
                "transformer": transformer,
                "max_error_rate": self._MAX_ERROR_RATE,
            }
        )
        # FIXME: ugly way to get more handler options from Transformer definition
        kwargs.update(getattr(transformer, "handler_options", {}))

        # allow user to override the default handler options
        if self.rendered_config.custom_handler_options:
            custom_handler_options = json.loads(self.rendered_config.custom_handler_options)
            kwargs.update(custom_handler_options)
        hf = create_csv_file_handler_factory(**kwargs)
        return hf

    def create_transformer(self) -> Transformer:
        transformer_code = self.rendered_config.get("transform", "").strip()
        if transformer_code:
            transformer = utils.validate_transform(transformer_code)
        else:
            transformer = None
        return transformer

    def has_custom_transformer(self):
        return self.rendered_config.get("transform")

    def get_schedule_time_range(self):
        end_date = self.execution_date
        start_date = self.dag.previous_schedule(self.execution_date)
        if self.config.get("time_auto_round", False):
            start_date = round_time_resolution(start_date, self.dag.schedule_interval)
            end_date = round_time_resolution(end_date, self.dag.schedule_interval)
        return start_date, end_date

    def remove_intermediate_files(self):
        pattern = f"{self.filename}.*"
        logger.info(f"remove intermediate files {pattern}")
        fs.remove_files_by_pattern(pattern)

    def on_execute_impl_error(self, exc: Exception):
        logger.exception(f"caught error: {exc}")
        self.remove_intermediate_files()


class LoadTask(Task):
    ds_types = ()
    should_write_header = False
    default_dumper_handler_options = {}
    dump_task_type = None

    def __init_subclass__(cls, **kwargs):
        _registry.add(cls)
        _load_task_registry.add(cls)

    @classmethod
    def type(cls):
        return "load"

    @property
    def stage(self) -> str:
        return "load"

    @staticmethod
    def compress_file(filename, target_filename=None, compress_mode="None"):
        """compress file before loading, only support gzip and zip"""
        if compress_mode == "None":
            return filename, None
        if compress_mode not in ("Gzip", "Zip", "Bzip2"):
            raise ValueError(f"{compress_mode} is not supported")

        logger.info(f"Compressing file using {compress_mode}")
        compress_method, ext = {
            "Gzip": (fs.gzip_compress, ".gz"),
            "Zip": (fs.zip_compress, ".zip"),
            "Bzip2": (fs.bzip2_compress, ".bz2"),
        }[compress_mode]

        # 如果指定了压缩包内的文件名，先把文件临时改名为目标文件名，压缩完了再改回来
        if target_filename:
            inner_filename = trim_suffix(os.path.basename(target_filename), ext)
            tmp_dir = tempfile.mkdtemp(dir=os.path.dirname(filename))
            file_to_compress = os.path.join(tmp_dir, inner_filename)
            os.rename(filename, file_to_compress)
        else:
            target_filename = f"{filename}{ext}"
            file_to_compress = filename

        try:
            compressed_file = compress_method(file_to_compress, target_filename=target_filename, using_cmd=True)
        except BaseException as e:
            raise e
        finally:
            # 如果发生异常，做回滚操作
            if file_to_compress != filename:
                os.rename(file_to_compress, filename)
                shutil.rmtree(os.path.dirname(file_to_compress))
        return compressed_file, ext


def get_task_class(name):
    return _registry[name]


def get_dump_classes():
    return sorted([x for x in _registry.values() if x.type() == "dump"], key=lambda x: x.name())


def get_load_classes():
    return sorted([x for x in _registry.values() if x.type() == "load"], key=lambda x: x.name())


def get_load_by_ds_type(ds_type):
    klass = _load_task_registry.get(ds_type)
    return klass.name()
