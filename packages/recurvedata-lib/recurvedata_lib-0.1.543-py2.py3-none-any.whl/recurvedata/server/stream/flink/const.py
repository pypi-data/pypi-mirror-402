# Flink SQL Gateway API Endpoints
FLINK_SQL_GATEWAY_SESSION_ENDPOINT = "/sessions"
FLINK_SQL_GATEWAY_STATEMENT_ENDPOINT = "/sessions/{session_handle}/statements"
FLINK_SQL_GATEWAY_OPERATION_ENDPOINT = "/sessions/{session_handle}/operations/{operation_handle}"


# Error Messages
ERROR_JOB_NOT_FOUND = "Job not found"
ERROR_INVALID_JOB_ID = "Invalid job ID"
ERROR_JOB_ALREADY_CANCELED = "Job is already canceled"
ERROR_JOB_CANCEL_FAILED = "Failed to cancel job"
ERROR_UNSUPPORTED_SOURCE_SINK_COMBINATION = "Unsupported source-sink combination"
ERROR_INVALID_FLINK_CONNECTION = "Invalid Flink connection"
ERROR_JOB_SUBMISSION_FAILED = "Job submission failed"
ERROR_FLINK_REST_API_ERROR = "Flink REST API error"

# Success Messages
SUCCESS_JOB_CREATED = "Job created successfully"
SUCCESS_JOB_CANCELED = "Job canceled successfully"
