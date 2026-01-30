from recurvedata.executors.utils import patch_pandas_mysql_connector_cext_missing

patch_pandas_mysql_connector_cext_missing()

from recurvedata.server.main import create_app  # noqa: E402

app = create_app()
