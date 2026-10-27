"""Feedback API endpoint (Part B2.14)."""
from typing import Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from services.api.app.core.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackRequest(BaseModel):
    message_id: UUID
    score: int = Field(..., ge=-1, le=1)  # -1 or +1
    comment: Optional[str] = None
    eval_case_id: Optional[UUID] = None

class FeedbackResponse(BaseModel):
    id: UUID
    status: str

_feedback_db = []

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    req: FeedbackRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    f_id = uuid4()
    _feedback_db.append({
        "id": f_id,
        "org_id": auth.org_id,
        "user_id": auth.user_id,
        "message_id": req.message_id,
        "score": req.score,
        "comment": req.comment,
    })
    return FeedbackResponse(id=f_id, status="recorded")
