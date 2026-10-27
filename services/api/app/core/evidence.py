"""Evidence Registry and Resolution Foundation (Part A3, Part A7, Section 12).
Target existence is validated by a registry where each module registers resolvers for its own target types.
"""
from typing import Any, Callable, Coroutine, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from packages.contracts.evidence import EvidenceResolution, EvidenceResolver, EvidenceTargetType
from services.api.app.core.errors import NotFoundError, ValidationError

TargetResolver = Callable[[AsyncSession, UUID, UUID], Coroutine[Any, Any, Optional[Dict[str, Any]]]]


class EvidenceRegistry:
    """Central registry validating evidence targets across modules."""

    _resolvers: Dict[str, Any] = {}

    def __init__(self):
        pass

    @classmethod
    def register_resolver(cls, target_type: str, resolver: Any) -> None:
        cls._resolvers[str(target_type)] = resolver

    @classmethod
    def has_resolver(cls, target_type: str) -> bool:
        return str(target_type) in cls._resolvers

    @classmethod
    async def resolve_target(
        cls, session: AsyncSession, org_id: UUID, target_type: str, target_id: UUID
    ) -> Optional[Dict[str, Any]]:
        resolver = cls._resolvers.get(str(target_type))
        if not resolver:
            return None
        if callable(resolver):
            try:
                return await resolver(session, org_id, target_id)
            except TypeError:
                return await resolver(org_id, target_id)
        return None

    def register(self, target_type: EvidenceTargetType, resolver: EvidenceResolver):
        self._resolvers[str(target_type)] = resolver

    async def resolve(
        self, org_id: UUID, target_type: EvidenceTargetType, target_id: UUID
    ) -> Optional[EvidenceResolution]:
        resolver = self._resolvers.get(str(target_type))
        if not resolver:
            return EvidenceResolution(
                target_type=target_type,
                target_id=target_id,
                title=f"Source [{target_type}]",
                snippet=f"Referenced record {str(target_id)[:8]} in {target_type}",
                metadata={"status": "unresolved_resolver"},
                org_id=org_id,
            )
        if hasattr(resolver, "resolve"):
            return await resolver.resolve(org_id, target_id)
        return None


evidence_registry = EvidenceRegistry()


async def create_claim_with_evidence(
    session: AsyncSession,
    org_id: UUID,
    decision_run_id: UUID,
    text: str,
    tag: str,
    status: str = "verified",
    target_type: Optional[str] = None,
    target_id: Optional[UUID] = None,
) -> Any:
    """Helper to create claims and optional 1:1 evidence links through core helpers."""
    from services.api.app.core.models import Claim, EvidenceLink

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
