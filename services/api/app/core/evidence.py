from typing import Any, Callable, Coroutine, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.app.core.errors import NotFoundError, ValidationError
from services.api.app.core.models import Claim, EvidenceLink

TargetResolver = Callable[[AsyncSession, UUID, UUID], Coroutine[Any, Any, Optional[Dict[str, Any]]]]


class EvidenceRegistry:
    """Central registry validating evidence targets across modules."""

    _resolvers: Dict[str, TargetResolver] = {}

    @classmethod
    def register_resolver(cls, target_type: str, resolver: TargetResolver) -> None:
        cls._resolvers[target_type] = resolver

    @classmethod
    def has_resolver(cls, target_type: str) -> bool:
        return target_type in cls._resolvers

    @classmethod
    async def resolve_target(
        cls, session: AsyncSession, org_id: UUID, target_type: str, target_id: UUID
    ) -> Optional[Dict[str, Any]]:
        resolver = cls._resolvers.get(target_type)
        if not resolver:
            # If no resolver registered yet (e.g. module still being built), allow gracefully or log
            return None
        return await resolver(session, org_id, target_id)


async def create_claim_with_evidence(
    session: AsyncSession,
    org_id: UUID,
    decision_run_id: UUID,
    text: str,
    tag: str,
    status: str = "verified",
    target_type: Optional[str] = None,
    target_id: Optional[UUID] = None,
) -> Claim:
    """Helper to create claims and optional 1:1 evidence links through core helpers."""
    if tag not in ("cited", "computed", "inferred", "commentary"):
        raise ValidationError(f"Invalid claim tag: {tag}")
    if status not in ("verified", "warning", "unverified", "failed"):
        raise ValidationError(f"Invalid claim status: {status}")

    claim = Claim(
        org_id=org_id,
        decision_run_id=decision_run_id,
        text=text,
        tag=tag,
        status=status,
    )
    session.add(claim)
    await session.flush()

    if target_type and target_id:
        # Validate target existence if resolver is available
        if EvidenceRegistry.has_resolver(target_type):
            resolved = await EvidenceRegistry.resolve_target(session, org_id, target_type, target_id)
            if not resolved:
                raise NotFoundError(f"Evidence target {target_type}:{target_id} not found in organization")

        link = EvidenceLink(
            org_id=org_id,
            claim_id=claim.id,
            target_type=target_type,
            target_id=target_id,
        )
        session.add(link)
        await session.flush()

    return claim
