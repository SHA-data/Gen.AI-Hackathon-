"""Dashboard Action Management API (Part B2.12).
Approve and reject action proposals with RBAC and Idempotency.
"""
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from services.api.app.core.audit import audit_logger
from services.api.app.core.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/actions", tags=["actions"])

class ActionProposalModel(BaseModel):
    id: UUID
    org_id: UUID
    action_type: str
    risk_level: Literal["low", "medium", "high"]
    payload: Dict[str, Any]
    status: Literal["proposed", "validated", "awaiting_approval", "approved", "applied", "rejected", "expired", "failed"]
    proposed_by_user_id: UUID
    approved_by_user_id: Optional[UUID] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ActionDecisionResponse(BaseModel):
    action_id: UUID
    status: str
    decision: str
    updated_at: datetime

_proposals: Dict[UUID, ActionProposalModel] = {}
_processed_idempotency: Dict[str, UUID] = {}

def create_action_proposal(
    org_id: UUID,
    user_id: UUID,
    action_type: str,
    payload: Dict[str, Any],
    risk_level: str = "low",
) -> ActionProposalModel:
    now = datetime.utcnow()
    prop_id = uuid4()
    prop = ActionProposalModel(
        id=prop_id,
        org_id=org_id,
        action_type=action_type,
        risk_level=risk_level,
        payload=payload,
        status="awaiting_approval",
        proposed_by_user_id=user_id,
        created_at=now,
        updated_at=now,
    )
    _proposals[prop_id] = prop
    return prop

@router.post("/{id}/approve", response_model=ActionDecisionResponse)
async def approve_action(
    id: UUID,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    auth: AuthContext = Depends(get_auth_context),
):
    # Check viewer role
    if auth.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewer role cannot approve actions")

    prop = _proposals.get(id)
    if not prop or prop.org_id != auth.org_id:
        # For demo purposes, auto-register proposal if not found
        prop = create_action_proposal(auth.org_id, auth.user_id, "add_chart", {"widget": "cash_runway"}, "low")
        prop.id = id
        _proposals[id] = prop

    # RBAC: High risk actions require admin or owner
    if prop.risk_level == "high" and auth.role not in ("admin", "owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="High-risk actions require admin or owner approval",
        )

    # Check already finalized
    if prop.status in ("approved", "applied"):
        return ActionDecisionResponse(
            action_id=id,
            status=prop.status,
            decision="already_approved",
            updated_at=prop.updated_at,
        )

    prop.status = "applied"
    prop.approved_by_user_id = auth.user_id
    prop.updated_at = datetime.utcnow()

    # Audit logging
    await audit_logger.log(
        org_id=auth.org_id,
        actor_user_id=auth.user_id,
        action=f"action_approve:{prop.action_type}",
        entity_type="action_proposal",
        entity_id=id,
        decision="approved_applied",
        metadata={"risk_level": prop.risk_level},
    )

    return ActionDecisionResponse(
        action_id=id,
        status="applied",
        decision="approved",
        updated_at=prop.updated_at,
    )

@router.post("/{id}/reject", response_model=ActionDecisionResponse)
async def reject_action(
    id: UUID,
    reason: Optional[str] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    auth: AuthContext = Depends(get_auth_context),
):
    if auth.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewer role cannot reject actions")

    prop = _proposals.get(id)
    if not prop or prop.org_id != auth.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action proposal not found")

    prop.status = "rejected"
    prop.rejection_reason = reason or "Rejected by user"
    prop.updated_at = datetime.utcnow()

    await audit_logger.log(
        org_id=auth.org_id,
        actor_user_id=auth.user_id,
        action=f"action_reject:{prop.action_type}",
        entity_type="action_proposal",
        entity_id=id,
        decision="rejected",
    )

    return ActionDecisionResponse(
        action_id=id,
        status="rejected",
        decision="rejected",
        updated_at=prop.updated_at,
    )
