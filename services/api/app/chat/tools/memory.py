"""Memory tools wrappers (Part A6, Part B2.10)."""
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from packages.contracts.envelope import ToolResultEnvelope
from packages.contracts.memory import FakeMemoryStore, MemoryItem, MemoryStore
from services.api.app.core.auth import AuthContext

_memory_store: MemoryStore = FakeMemoryStore()

def set_memory_store(store: MemoryStore):
    global _memory_store
    _memory_store = store

def get_memory_store() -> MemoryStore:
    return _memory_store

class MemoryReadArgs(BaseModel):
    category: Optional[str] = None
    key: Optional[str] = None

class MemoryWriteArgs(BaseModel):
    category: str
    key: str
    value: str

async def handle_memory_read(auth: AuthContext, category: Optional[str] = None, key: Optional[str] = None) -> ToolResultEnvelope[List[Dict[str, Any]]]:
    items = await _memory_store.read(org_id=auth.org_id, user_id=auth.user_id, category=category, key=key)
    return ToolResultEnvelope(
        status="ok",
        data=[item.model_dump() for item in items],
        sources=[item.id for item in items],
        warnings=[],
        run_id=None,
    )

async def handle_memory_write(auth: AuthContext, category: str, key: str, value: str) -> ToolResultEnvelope[Dict[str, Any]]:
    # Propose the memory item; user must confirm
    item = await _memory_store.propose(
        org_id=auth.org_id,
        user_id=auth.user_id,
        category=category,
        key=key,
        value=value,
    )
    return ToolResultEnvelope(
        status="ok",
        data={
            "proposed_memory": item.model_dump(),
            "confirmation_required": True,
            "message": f"Proposed memory for key '{key}'. Awaiting user confirmation.",
        },
        sources=[item.id],
        warnings=[],
        run_id=item.id,
    )
