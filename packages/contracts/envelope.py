"""Shared envelopes for API responses and tool results across all modules."""
from enum import Enum
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

T = TypeVar("T")


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
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: str(uuid4()))


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class ToolResultEnvelope(BaseModel, Generic[T]):
    """Standard tool envelope defined in Part A2.
    {"status": "ok|warning|failed", "data": {}, "sources": [], "warnings": [], "run_id": "uuid|null"}
    """
    status: Union[ToolStatus, Literal["ok", "warning", "failed"], str]
    data: T
    sources: List[Union[UUID, str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    run_id: Optional[Union[UUID, str]] = None
