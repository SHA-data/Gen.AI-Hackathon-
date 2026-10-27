"""Conversations API routes (Part B2.3)."""
from datetime import datetime
from typing import Dict, List, Literal, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.api.app.core.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/conversations", tags=["conversations"])

class CreateConversationRequest(BaseModel):
    agent_key: Literal["neuralcfo", "moonshot", "router"] = "router"
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: UUID
    org_id: UUID
    user_id: UUID
    agent_key: str
    title: str
    created_at: datetime
    updated_at: datetime

# In-memory store for standalone mode before database migration is applied
_conversations: Dict[UUID, ConversationResponse] = {}

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: CreateConversationRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    conv_id = uuid4()
    now = datetime.utcnow()
    conv = ConversationResponse(
        id=conv_id,
        org_id=auth.org_id,
        user_id=auth.user_id,
        agent_key=req.agent_key,
        title=req.title or "New Conversation",
        created_at=now,
        updated_at=now,
    )
    _conversations[conv_id] = conv
    return conv

@router.get("/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: UUID,
    auth: AuthContext = Depends(get_auth_context),
):
    conv = _conversations.get(id)
    # Check tenant isolation
    if not conv or conv.org_id != auth.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv
