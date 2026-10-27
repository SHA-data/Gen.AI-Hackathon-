"""Evidence and claim contracts (Part A3, Part A7, Section 12)."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Protocol
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

ClaimTag = Literal["cited", "computed", "inferred", "commentary"]

EvidenceTargetType = Literal[
    "source_row",
    "financial_record",
    "forecast_run",
    "forecast_point",
    "finance_assumption",
    "goal_assumption",
    "document_chunk",
    "web_source",
    "kb_excerpt",
    "strategy_score",
    "base_rate",
]

class EvidenceLink(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    claim_id: UUID
    target_type: EvidenceTargetType
    target_id: UUID

class Claim(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    decision_run_id: UUID
    text: str
    tag: ClaimTag
    status: Literal["verified", "warning", "unverified", "failed"] = "verified"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EvidenceResolution(BaseModel):
    target_type: EvidenceTargetType
    target_id: UUID
    title: str
    snippet: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    org_id: UUID

class EvidenceResolver(Protocol):
    """Protocol for target type resolvers registered in app/core/evidence.py."""
    async def resolve(self, org_id: UUID, target_id: UUID) -> Optional[EvidenceResolution]:
        ...
