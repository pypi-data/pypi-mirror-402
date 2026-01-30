"""
copied from recurve-server
"""

from recurvedata.error_codes import BaseErrorCode


class ErrorCode(BaseErrorCode):
    MODEL_COMPILE_FAILED = ("A1301", "Model compile failed")
    MODEL_PREVIEW_FAILED = ("A1302", "Model preview failed")
    DEPS_FAILED = ("A1303", "DBT deps failed")
    DP_FETCH_PROJECT_FAILED = ("A1304", "DP fetch project failed")
    DP_FETCH_CONNECTION_FAILED = ("A1305", "DP fetch connection failed")
    DP_FETCH_VARIABLE_FAILED = ("A1306", "DP fetch variable failed")
    MODEL_RUN_FAILED = ("A1307", "Model run failed")


ERR = ErrorCode  # shortcut
