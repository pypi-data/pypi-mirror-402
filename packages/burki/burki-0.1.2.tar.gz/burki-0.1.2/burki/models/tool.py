"""
Tool models for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HTTPToolConfig(BaseModel):
    """Configuration for an HTTP API tool."""
    
    method: str = "GET"
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    body_template: Optional[str] = None
    timeout: int = 30


class PythonToolConfig(BaseModel):
    """Configuration for a Python function tool."""
    
    code: str
    requirements: List[str] = Field(default_factory=list)
    timeout: int = 30


class LambdaToolConfig(BaseModel):
    """Configuration for an AWS Lambda tool."""
    
    function_arn: str
    region: str = "us-east-1"
    invocation_type: str = "RequestResponse"
    timeout: int = 30


class ToolParameter(BaseModel):
    """A parameter for a tool."""
    
    name: str
    type: str = "string"
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[str]] = None


class Tool(BaseModel):
    """Represents a tool in Burki."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    organization_id: int
    
    name: str
    description: Optional[str] = None
    tool_type: str  # http, python, lambda
    
    parameters: List[ToolParameter] = Field(default_factory=list)
    
    # Type-specific configuration
    http_config: Optional[HTTPToolConfig] = None
    python_config: Optional[PythonToolConfig] = None
    lambda_config: Optional[LambdaToolConfig] = None
    
    is_active: bool = True
    
    # Usage stats
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time: Optional[float] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ToolCreate(BaseModel):
    """Request model for creating a tool."""
    
    name: str
    description: Optional[str] = None
    tool_type: str  # http, python, lambda
    
    parameters: List[ToolParameter] = Field(default_factory=list)
    
    http_config: Optional[HTTPToolConfig] = None
    python_config: Optional[PythonToolConfig] = None
    lambda_config: Optional[LambdaToolConfig] = None


class ToolUpdate(BaseModel):
    """Request model for updating a tool."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    parameters: Optional[List[ToolParameter]] = None
    
    http_config: Optional[HTTPToolConfig] = None
    python_config: Optional[PythonToolConfig] = None
    lambda_config: Optional[LambdaToolConfig] = None


class ToolList(BaseModel):
    """Response model for listing tools."""
    
    items: List[Tool]
    total: int


class ToolAssignment(BaseModel):
    """Request model for assigning a tool to an assistant."""
    
    assistant_id: int


class LambdaFunction(BaseModel):
    """An AWS Lambda function discovered for tool creation."""
    
    function_name: str
    function_arn: str
    description: Optional[str] = None
    runtime: Optional[str] = None
    handler: Optional[str] = None
    memory_size: Optional[int] = None
    timeout: Optional[int] = None
    last_modified: Optional[str] = None


class LambdaDiscoveryResult(BaseModel):
    """Result of Lambda function discovery."""
    
    functions: List[LambdaFunction]
    region: str
    total: int


class ToolExecution(BaseModel):
    """Result of a tool execution."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tool_id: int
    call_id: Optional[int] = None
    status: str  # success, failure, timeout
    input_params: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    executed_at: Optional[datetime] = None


# Re-export all models
__all__ = [
    "Tool",
    "ToolCreate",
    "ToolUpdate",
    "ToolList",
    "ToolParameter",
    "ToolExecution",
    "HTTPToolConfig",
    "PythonToolConfig",
    "LambdaToolConfig",
    "ToolAssignment",
    "LambdaFunction",
    "LambdaDiscoveryResult",
]
