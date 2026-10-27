"""Main Chatbot API Router with /v1 prefix."""
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.api.app.chat.api.actions import router as actions_router
from services.api.app.chat.api.citations import router as citations_router
from services.api.app.chat.api.conversations import router as conversations_router
from services.api.app.chat.api.documents import router as documents_router
from services.api.app.chat.api.feedback import router as feedback_router
from services.api.app.chat.api.memories import router as memories_router
from services.api.app.chat.api.messages import router as messages_router
from services.api.app.chat.api.stt import router as stt_router
from services.api.app.core.auth import (
    DEMO_ORG_A,
    DEMO_ORG_B,
    DEMO_USER_A_ADMIN,
    DEMO_USER_A_MEMBER,
    DEMO_USER_A_VIEWER,
    DEMO_USER_B_MEMBER,
    RoleType,
    create_access_token,
)
from services.api.app.core.config import settings

v1_router = APIRouter(prefix="/v1")

# Mount module routers
v1_router.include_router(conversations_router)
v1_router.include_router(messages_router)
v1_router.include_router(documents_router)
v1_router.include_router(actions_router)
v1_router.include_router(memories_router)
v1_router.include_router(citations_router)
v1_router.include_router(feedback_router)
v1_router.include_router(stt_router)

# Development token minting endpoint per Part A4
class DevTokenRequest(BaseModel):
    user_id: UUID
    org_id: UUID
    role: RoleType

class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    org_id: UUID
    role: str

@v1_router.post("/dev/token", response_model=DevTokenResponse)
async def mint_dev_token(req: DevTokenRequest):
    if settings.ENV not in ("dev", "test"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dev token minting is disabled in production")
    token = create_access_token(user_id=req.user_id, org_id=req.org_id, role=req.role)
    return DevTokenResponse(
        access_token=token,
        user_id=req.user_id,
        org_id=req.org_id,
        role=req.role,
    )
