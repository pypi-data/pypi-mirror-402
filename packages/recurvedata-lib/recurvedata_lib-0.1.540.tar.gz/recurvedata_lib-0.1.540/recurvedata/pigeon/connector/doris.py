import json
import subprocess
import time

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.mysql import MySQLConnector
from recurvedata.pigeon.schema import types

_canonical_type_to_doris_type = {
    types.BOOLEAN: "TINYINT",
    types.INT8: "TINYINT",
    types.INT16: "SMALLINT",
    types.INT32: "INT",
    types.INT64: "BIGINT",
    types.FLOAT32: "FLOAT",
    types.FLOAT64: "DOUBLE",
    types.DATE: "DATE",
    types.DATETIME: "DATETIME",
    types.STRING: "STRING",
    types.JSON: "STRING",
}


@register_connector_class(["doris"])
class DorisConnector(MySQLConnector):
    _sqla_driver = "doris+pymysql"
    _default_port = 9030
    _default_fe_http_port = 8030

    def __init__(self, host, port=None, http_port=None, database=None, user=None, password=None, *args, **kwargs):
        self.http_port = http_port or self._default_fe_http_port
        super().__init__(host=host, port=port, database=database, user=user, password=password, *args, **kwargs)

    @property
    def load_strict_mode(self):
        if not hasattr(self, "_load_strict_mode"):
            return False
        return self._load_strict_mode

    @load_strict_mode.setter
    def load_strict_mode(self, mode: bool):
        self._load_strict_mode = mode

    @property
    def max_filter_ratio(self):
        if not hasattr(self, "_max_filter_ratio"):
            return 0
        return self._max_filter_ratio

    def has_table(self, table, database=None, cursor=None, **kwargs):
        retry_num = 6
        for attempt in range(retry_num):
            if super().has_table(table, database, cursor, **kwargs):
                return True
            if attempt < retry_num - 1:
                wait_time = (attempt + 1) ** 2
                time.sleep(wait_time)  # wait for table to be created and visible
        return False

    @max_filter_ratio.setter
    def max_filter_ratio(self, ratio: float):
        if ratio < 0:
            self._max_filter_ratio = 0
        elif ratio > 1:
            self._max_filter_ratio = 1
        else:
            self._max_filter_ratio = ratio

    def _load_csv_mysql(
        self,
        table,
        filename,
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        **kwargs,
    ):
        """
        stream load data from csv file into table
        """

        def _split_database_table(table_name: str):
            tmp_lst = table_name.split(".")
            if len(tmp_lst) == 1:
                return self.database, table_name
            return tmp_lst

        db_name, table_name = _split_database_table(table)
        shell_cmd = self._format_load_shell(filename, db_name, table_name)

        # Set only authentication environment variables
        _env = {}
        if self.user is not None:
            _env["DORIS_USER"] = self.user
        if self.password is not None:
            _env["DORIS_PASSWORD"] = self.password

        output = subprocess.check_output(shell_cmd, env=_env, shell=True)
        self._log(output)
        res_txt = output.decode()
        res = json.loads(res_txt)
        self._log(res_txt)

        if res["Status"] != "Success":
            if "ErrorURL" not in res:
                err_output = res["Message"]
            else:
                err_url = res["ErrorURL"]
                err_output = subprocess.check_output(["curl", err_url])
            self._log(f"error: {err_output}")
            raise Exception("load csv failed")

    def _format_load_shell(self, filename: str, db_name: str, table_name: str) -> str:
        """Format the curl command for Doris stream load.

        Args:
            filename: Path to the CSV file to load
            db_name: Target database name
            table_name: Target table name

        Returns:
            Formatted curl command string for stream loading data
        """

        def __format_column_mapping(db_name: str, table_name: str) -> str:
            columns = self.get_columns(table_name, db_name)
            cols_txt = ",".join(columns)
            return f"columns: {cols_txt}"

        def __format_stream_load_url(db_name: str, table_name: str) -> str:
            return f"http://{self.host}:{self.http_port}/api/{db_name}/{table_name}/_stream_load"

        # Clean table and db names
        db_name = db_name.strip("`")
        table_name = table_name.strip("`")

        # Build command components
        url = __format_stream_load_url(db_name, table_name)
        strict_mode = "true" if self.load_strict_mode else "false"
        column_mapping = __format_column_mapping(db_name, table_name)

        # Construct the full curl command with properly escaped quotes
        return (
            f"curl --location-trusted -u $DORIS_USER:$DORIS_PASSWORD "
            f'-H "Expect:100-continue" '
            f'-H "max_filter_ratio:{self.max_filter_ratio}" '
            f'-H "column_separator:," '
            f'-H "enclose:\\"" '
            f'-H "trim_double_quotes:true" '
            f'-H "strict_mode:{strict_mode}" '
            f'-H "escape:\'" '
            f'-H "{column_mapping}" '
            f"-T {filename} -XPUT "
            f"{url}"
        ).strip()

    @staticmethod
    def from_canonical_type(canonical_type, size):
        if canonical_type == types.STRING:
            doris_type = "STRING"
        else:
            doris_type = _canonical_type_to_doris_type.get(canonical_type, "STRING")
        return doris_type
