from recurvedata.error_codes import BaseErrorCode


class ErrorCode(BaseErrorCode):
    # stream operator
    STREAM_OPERATOR_EXECUTION_FAILED = ("A1701", "Stream operator execution failed")
    STREAM_OPERATOR_NO_COLUMNS_FOUND = ("A1702", "No columns found for table in schema of database")
    STREAM_OPERATOR_TABLE_NOT_FOUND = ("A1703", "Table not found in schema / database")


ERR = ErrorCode  # shortcut
