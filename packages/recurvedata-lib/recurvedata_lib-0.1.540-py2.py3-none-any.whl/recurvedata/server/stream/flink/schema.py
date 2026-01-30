"""Pydantic schemas for Flink Stream API endpoints"""

from datetime import datetime
from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field

from recurvedata.executors.schemas import ResponseModel


class FlinkJobStatus(str, Enum):
    """Flink job status enumeration"""

    INITIALIZING = "INITIALIZING"
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    FAILING = "FAILING"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELED = "CANCELED"
    FINISHED = "FINISHED"
    RESTARTING = "RESTARTING"
    SUSPENDED = "SUSPENDED"
    RECONCILING = "RECONCILING"


class SourceConfig(BaseModel):
    """CDC source configuration"""

    connection_name: str
    source_type: str | None = Field(None, description="Database type (mysql, postgres, mongodb, etc.)")
    database_name: str | None = None
    schema_name: str | None = None
    table_name: str
    slot_name: str | None = None


class SinkConfig(BaseModel):
    """CDC sink configuration"""

    connection_name: str
    sink_type: str | None = Field(None, description="Database type (mysql, postgres, doris, etc.)")
    database_name: str | None = None
    schema_name: str | None = None
    table_name: str | None = None


class FlinkConfig(BaseModel):
    """Flink job configuration"""

    flink_connection_name: str
    checkpoint_interval: int = Field(default=3000, ge=1000)
    parallelism: int = Field(default=2, ge=1, le=32)
    max_parallelism: int | None = Field(default=None, ge=1, le=32768)
    restart_strategy: str | None = Field(default="fixed-delay")


class TransformConfig(BaseModel):
    """Data transformation configuration"""

    sql: str | None = None
    unique_key: str


# API Request Payloads
class CreateJobPayload(BaseModel):
    """Payload for creating a new Flink CDC job"""

    job_name: str = Field(..., min_length=1, max_length=1024)
    source: SourceConfig
    sink: SinkConfig
    flink_config: FlinkConfig
    transform: TransformConfig
    project_id: int


class CancelJobPayload(BaseModel):
    """Payload for canceling a Flink job"""

    job_id: str
    flink_connection_name: str
    project_id: int
    source_config: SourceConfig | None = None  # For cleanup (e.g., PostgreSQL replication slots)


# API Response Models
class JobDetails(BaseModel):
    """Flink job details"""

    job_id: str
    job_name: str
    description: str | None = None
    status: FlinkJobStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: int | None = None  # Duration in milliseconds
    parallelism: int
    exceptions: List[Dict] | None = Field(default_factory=list)


class CreateJobData(BaseModel):
    job_id: str | None = None
    job_name: str
    status: FlinkJobStatus
    message: str | None = None


class CreateJobResponse(ResponseModel):
    """Response for job creation"""

    data: CreateJobData | None


class CancelJobResponse(ResponseModel):
    """Response for job cancellation"""

    data: str | None


class GetJobStatusResponse(BaseModel):
    """Response for job status query"""

    job_details: JobDetails


class GetJobDetailsResponse(ResponseModel):
    data: JobDetails | None


class JobSummary(BaseModel):
    """Summary information for a job in list view"""

    job_id: str
    job_name: str
    status: FlinkJobStatus
    start_time: datetime | None = None
    duration: int | None = None


class GetJobsResponse(ResponseModel):
    """Response for jobs list"""

    data: List[JobSummary] | None


# Response wrappers using the standard ResponseModel pattern
class CreateJobResponseWrapper(ResponseModel):
    data: CreateJobResponse | None = None


class CancelJobResponseWrapper(ResponseModel):
    data: CancelJobResponse | None = None


class GetJobStatusResponseWrapper(ResponseModel):
    data: GetJobStatusResponse | None = None


class GetJobsResponseWrapper(ResponseModel):
    data: GetJobsResponse | None = None


class SqlGatewayClientExecuteStatementResponse(BaseModel):
    job_id: str | None = None
    error: str | None = None
