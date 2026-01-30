import json
import subprocess

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.mysql import MySQLConnector
from recurvedata.pigeon.schema import types

_canonical_type_to_starrocks_type = {
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


@register_connector_class(["starrocks"])
class StarRocksConnector(MySQLConnector):
    _default_port = 9030
    _default_fe_http_port = 8030

    def __init__(self, host, port=None, http_port=None, database=None, user=None, password=None, *args, **kwargs):
        self.http_port = http_port or self._default_fe_http_port
        self.user = user
        self.password = password
        super().__init__(host=host, port=port, database=database, user=user, password=password, *args, **kwargs)

    @property
    def load_strict_mode(self) -> bool:
        if not hasattr(self, "_load_strict_mode"):
            return False
        return self._load_strict_mode

    @load_strict_mode.setter
    def load_strict_mode(self, mode: bool):
        self._load_strict_mode = mode

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
            _env["STARROCKS_USER"] = self.user
        if self.password is not None:
            _env["STARROCKS_PASSWORD"] = self.password

        output = subprocess.check_output(shell_cmd, env=_env, shell=True)
        res_txt = output.decode()
        if res_txt:
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
        def __format_column_mapping(db_name: str, table_name: str) -> str:
            """
            stream load 有个 bug，最后一列的右引号无法去除
            在 column_mapping 里处理
            """
            columns = self.get_columns(table_name, db_name)
            # Extract column names from the column metadata
            column_names = [col["name"] for col in columns]
            # Escape backticks to prevent shell interpretation
            cols = [f"\\`{col}\\`" for col in column_names]
            cols_txt = ",".join(cols)
            cols2 = [
                f"\\`{col}\\`=trim(\\`{col}\\`,'\\\"')" if col == column_names[-1] else f"\\`{col}\\`=\\`{col}\\`"
                for col in column_names
            ]
            cols_txt2 = ", ".join(cols2)
            return f"columns: {cols_txt}, {cols_txt2}"

        def __format_stream_load_url(db_name: str, table_name: str) -> str:
            return f"http://{self.host}:{self.http_port}/api/{db_name}/{table_name}/_stream_load"

        db_name, table_name = db_name.strip("`"), table_name.strip("`")
        url = __format_stream_load_url(db_name, table_name)
        strict_mode = "true" if self.load_strict_mode else "false"
        column_mapping = __format_column_mapping(db_name, table_name)

        # Handle authentication based on whether password is provided
        if self.password is not None:
            auth_part = "-u $STARROCKS_USER:$STARROCKS_PASSWORD"
        else:
            auth_part = "-u $STARROCKS_USER:"

        # Construct the full curl command with properly escaped quotes
        return (
            f"curl --location-trusted {auth_part} "
            f'-H "Expect:100-continue" '
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
            starrocks_type = "STRING"
        else:
            starrocks_type = _canonical_type_to_starrocks_type.get(canonical_type, "STRING")
        return starrocks_type
