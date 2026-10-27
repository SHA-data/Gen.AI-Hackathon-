"""Evidence Registry and Resolution Foundation (Part A3, Part A7, Section 12).
Target existence is validated by a registry where each module registers resolvers for its own target types.
"""
from typing import Dict, Optional
from uuid import UUID
from packages.contracts.evidence import EvidenceResolution, EvidenceResolver, EvidenceTargetType

class EvidenceRegistry:
    def __init__(self):
        self._resolvers: Dict[EvidenceTargetType, EvidenceResolver] = {}

    def register(self, target_type: EvidenceTargetType, resolver: EvidenceResolver):
        self._resolvers[target_type] = resolver

    async def resolve(
        self, org_id: UUID, target_type: EvidenceTargetType, target_id: UUID
    ) -> Optional[EvidenceResolution]:
        resolver = self._resolvers.get(target_type)
        if not resolver:
            # Fallback placeholder if owning module has not registered yet
            return EvidenceResolution(
                target_type=target_type,
                target_id=target_id,
                title=f"Source [{target_type}]",
                snippet=f"Referenced record {str(target_id)[:8]} in {target_type}",
                metadata={"status": "unresolved_resolver"},
                org_id=org_id,
            )
        return await resolver.resolve(org_id, target_id)

evidence_registry = EvidenceRegistry()
