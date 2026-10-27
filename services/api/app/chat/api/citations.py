"""Citations API endpoint (Part B2.9).
Resolves evidence links through the core evidence registry.
"""
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from services.api.app.core.auth import AuthContext, get_auth_context
from services.api.app.core.evidence import evidence_registry

router = APIRouter(prefix="/citations", tags=["citations"])

class CitationResponse(BaseModel):
    id: UUID
    target_type: str
    target_id: UUID
    title: str
    snippet: str
    metadata: Dict[str, Any]

@router.get("/{id}", response_model=CitationResponse)
async def get_citation(
    id: UUID,
    auth: AuthContext = Depends(get_auth_context),
):
    # Resolve against evidence registry (default target_type is forecast_point / source_row)
    res = await evidence_registry.resolve(org_id=auth.org_id, target_type="forecast_point", target_id=id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found or inaccessible")

    # Enforce tenant isolation
    if res.org_id != auth.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found in this organization")

    return CitationResponse(
        id=id,
        target_type=res.target_type,
        target_id=res.target_id,
        title=res.title,
        snippet=res.snippet,
        metadata=res.metadata,
    )
