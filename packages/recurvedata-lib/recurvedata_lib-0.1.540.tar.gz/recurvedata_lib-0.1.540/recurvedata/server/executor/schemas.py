from typing import Optional

from pydantic import BaseModel, Field

from recurvedata.executors.schemas import ResponseModel


class ValidatePythonScriptPayload(BaseModel):
    """Payload for Python script validation request"""
    
    project_id: int = Field(..., description="Project ID")
    python_code: str = Field(..., description="Python code to validate")
    python_env: str = Field(..., description="Python environment connection name")
    timeout: int = Field(default=30, description="Validation timeout in seconds")


class PythonScriptValidationResult(BaseModel):
    """Result of Python script validation"""
    
    valid: bool = Field(..., description="Whether the script is valid")
    message: str = Field(default="", description="Validation message")
    error: Optional[dict] = Field(default=None, description="Error details if validation failed")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")
    installed_requirements: Optional[str] = Field(default=None, description="Installed requirements")


class ValidatePythonScriptResponse(ResponseModel):
    """Response for Python script validation"""
    
    data: Optional[PythonScriptValidationResult] = None
