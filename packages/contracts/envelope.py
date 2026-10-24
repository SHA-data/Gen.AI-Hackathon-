from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ResultStatus(str, Enum):
    VERIFIED = "verified"
    WARNING = "warning"
    UNVERIFIED = "unverified"
    FAILED = "failed"


class ToolStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    FAILED = "failed"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class ToolResultEnvelope(BaseModel):
    status: ToolStatus
    data: Dict[str, Any] = Field(default_factory=dict)
    sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    run_id: Optional[str] = None
