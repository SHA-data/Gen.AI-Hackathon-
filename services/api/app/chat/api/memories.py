"""Memories API endpoint (Part B2.10).
View, correct, and delete user and organization memories.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from packages.contracts.memory import MemoryItem
from services.api.app.chat.tools.memory import get_memory_store
from services.api.app.core.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/memories", tags=["memories"])

class UpdateMemoryRequest(BaseModel):
    value: str

@router.get("", response_model=List[MemoryItem])
async def list_memories(
    category: Optional[str] = None,
    auth: AuthContext = Depends(get_auth_context),
):
    store = get_memory_store()
    return await store.read(org_id=auth.org_id, user_id=auth.user_id, category=category, status=None)

@router.patch("/{id}", response_model=MemoryItem)
async def update_memory(
    id: UUID,
    req: UpdateMemoryRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    store = get_memory_store()
    try:
        return await store.update(org_id=auth.org_id, memory_id=id, value=req.value)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    id: UUID,
    auth: AuthContext = Depends(get_auth_context),
):
    store = get_memory_store()
    deleted = await store.delete(org_id=auth.org_id, memory_id=id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return None
