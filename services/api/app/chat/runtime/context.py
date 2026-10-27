"""Execution Context for Chat turns."""
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from services.api.app.core.auth import AuthContext
from packages.contracts.envelope import ToolResultEnvelope

class TurnCitation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    claim_id: Optional[UUID] = None
    target_type: str
    target_id: UUID
    label: str
    snippet: Optional[str] = None

class ExecutionContext(BaseModel):
    conversation_id: UUID
    decision_run_id: UUID = Field(default_factory=uuid4)
    auth: AuthContext
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    executed_tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[ToolResultEnvelope[Any]] = Field(default_factory=list)
    citations: List[TurnCitation] = Field(default_factory=list)
    stages: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {
        "arbitrary_types_allowed": True,
    }
