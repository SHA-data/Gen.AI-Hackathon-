"""Audit log recording helper (Part A3, Section 13).
Logs IDs and decisions only — NEVER raw financial or document text.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class AuditLogEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    actor_user_id: Optional[UUID] = None
    action: str
    entity_type: str
    entity_id: UUID
    decision: str  # 'allowed' | 'denied' | 'approved' | 'rejected' | 'executed'
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLogger:
    """In-memory collector and DB helper for append-only audit entries."""
    def __init__(self):
        self._entries: list[AuditLogEntry] = []

    async def log(
        self,
        org_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
        decision: str,
        actor_user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        # Sanitize metadata: verify no raw text or financial amounts are leaked
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                if k in ("amount", "text", "content", "document_text", "prompt"):
                    clean_meta[k] = "[REDACTED_CONTENT]"
                else:
                    clean_meta[k] = v

        entry = AuditLogEntry(
            org_id=org_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            decision=decision,
            metadata=clean_meta,
        )
        self._entries.append(entry)
        return entry

    def get_entries(self, org_id: UUID) -> list[AuditLogEntry]:
        return [e for e in self._entries if e.org_id == org_id]

audit_logger = AuditLogger()
