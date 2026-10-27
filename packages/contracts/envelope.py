"""Shared envelopes for API responses and tool results across all modules."""
from typing import Any, Generic, List, Literal, Optional, TypeVar
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

T = TypeVar("T")

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
    status: Literal["ok", "warning", "failed"]
    data: T
    sources: List[UUID] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    run_id: Optional[UUID] = None
