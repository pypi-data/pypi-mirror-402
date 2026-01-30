from recurvedata.executors.utils import patch_pandas_mysql_connector_cext_missing

patch_pandas_mysql_connector_cext_missing()

from recurvedata.executors.cli.main import cli  # noqa: E402

__all__ = ["cli"]
