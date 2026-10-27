"""Memory Store protocol and Fake implementation (Part B0.3, B2.10)."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Protocol
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

MemoryStatus = Literal["proposed", "confirmed", "rejected", "archived"]

class MemoryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    user_id: UUID
    category: str
    key: str
    value: str
    status: MemoryStatus = "proposed"
    source_message_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MemoryTrace(BaseModel):
    memory_id: UUID
    history: List[Dict[str, Any]]
    backend: str

class MemoryStore(Protocol):
    """Protocol for memory backends (Postgres and Meterless)."""
    async def read(
        self,
        org_id: UUID,
        user_id: UUID,
        category: Optional[str] = None,
        key: Optional[str] = None,
        status: Optional[MemoryStatus] = "confirmed",
    ) -> List[MemoryItem]:
        ...

    async def propose(
        self,
        org_id: UUID,
        user_id: UUID,
        category: str,
        key: str,
        value: str,
        source_message_id: Optional[UUID] = None,
    ) -> MemoryItem:
        ...

    async def confirm(self, org_id: UUID, memory_id: UUID) -> MemoryItem:
        ...

    async def delete(self, org_id: UUID, memory_id: UUID) -> bool:
        ...

    async def update(self, org_id: UUID, memory_id: UUID, value: str) -> MemoryItem:
        ...

    async def trace(self, org_id: UUID, memory_id: UUID) -> MemoryTrace:
        ...

class FakeMemoryStore:
    """In-memory store simulating persistent memory across sessions."""
    def __init__(self):
        self._items: Dict[UUID, MemoryItem] = {}

    async def read(
        self,
        org_id: UUID,
        user_id: UUID,
        category: Optional[str] = None,
        key: Optional[str] = None,
        status: Optional[MemoryStatus] = "confirmed",
    ) -> List[MemoryItem]:
        results = []
        for item in self._items.values():
            if item.org_id == org_id and item.user_id == user_id:
                if status and item.status != status:
                    continue
                if category and item.category != category:
                    continue
                if key and item.key != key:
                    continue
                results.append(item)
        return results

    async def propose(
        self,
        org_id: UUID,
        user_id: UUID,
        category: str,
        key: str,
        value: str,
        source_message_id: Optional[UUID] = None,
    ) -> MemoryItem:
        item = MemoryItem(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            status="proposed",
            source_message_id=source_message_id,
        )
        self._items[item.id] = item
        return item

    async def confirm(self, org_id: UUID, memory_id: UUID) -> MemoryItem:
        item = self._items.get(memory_id)
        if not item or item.org_id != org_id:
            raise KeyError(f"Memory {memory_id} not found")
        item.status = "confirmed"
        item.updated_at = datetime.utcnow()
        return item

    async def delete(self, org_id: UUID, memory_id: UUID) -> bool:
        item = self._items.get(memory_id)
        if not item or item.org_id != org_id:
            return False
        del self._items[memory_id]
        return True

    async def update(self, org_id: UUID, memory_id: UUID, value: str) -> MemoryItem:
        item = self._items.get(memory_id)
        if not item or item.org_id != org_id:
            raise KeyError(f"Memory {memory_id} not found")
        item.value = value
        item.updated_at = datetime.utcnow()
        return item

    async def trace(self, org_id: UUID, memory_id: UUID) -> MemoryTrace:
        item = self._items.get(memory_id)
        if not item or item.org_id != org_id:
            raise KeyError(f"Memory {memory_id} not found")
        return MemoryTrace(
            memory_id=memory_id,
            backend="fake_memory_store",
            history=[
                {"timestamp": item.created_at.isoformat(), "action": "created", "status": "proposed"},
                {"timestamp": item.updated_at.isoformat(), "action": "state_change", "status": item.status},
            ],
        )
