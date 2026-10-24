from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.app.core.models import AuditLog


async def create_audit_log(
    session: AsyncSession,
    org_id: UUID,
    action: str,
    entity_type: str,
    actor_user_id: Optional[UUID] = None,
    entity_id: Optional[UUID] = None,
    decision: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Append-only audit log entry helper.

    Per PDF rules: logs must record ids, actions and decisions, not full financial content.
    """
    safe_metadata = metadata or {}
    audit_entry = AuditLog(
        org_id=org_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        decision=decision,
        extra_metadata=safe_metadata,
    )
    session.add(audit_entry)
    await session.flush()
    return audit_entry
