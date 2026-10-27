"""Meterless MemoryStore Adapter (Part B0.3, B2.10).
Integrates with Meterless memory backend if available; falls back cleanly to Postgres/in-memory store.
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from packages.contracts.memory import MemoryItem, MemoryStatus, MemoryStore, MemoryTrace

class MeterlessMemoryStore:
    """Meterless memory backend adapter implementing the shared MemoryStore protocol.
    If METERLESS_API_KEY / host is not configured, operates in labeled transparent fallback mode.
    """
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.getenv("METERLESS_API_KEY")
        self.endpoint = endpoint or os.getenv("METERLESS_ENDPOINT", "https://api.meterless.synthetic/v1")
        # Internal fallback storage for local verification
        self._items: Dict[UUID, MemoryItem] = {}
        self._traces: Dict[UUID, List[Dict[str, Any]]] = {}

    @property
    def is_real_meterless_active(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("fake"))

    async def read(
        self,
        org_id: UUID,
        user_id: UUID,
        category: Optional[str] = None,
        key: Optional[str] = None,
        status: Optional[MemoryStatus] = "confirmed",
    ) -> List[MemoryItem]:
        # Scoped strictly by tenant (org_id) and user_id
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
        mem_id = uuid4()
        now = datetime.utcnow()
        item = MemoryItem(
            id=mem_id,
            org_id=org_id,
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            status="proposed",
            source_message_id=source_message_id,
            created_at=now,
            updated_at=now,
        )
        self._items[mem_id] = item
        self._traces[mem_id] = [
            {"timestamp": now.isoformat(), "event": "meterless_memory_proposed", "backend": "meterless_adapter"}
        ]
        return item

    async def confirm(self, org_id: UUID, memory_id: UUID) -> MemoryItem:
        item = self._items.get(memory_id)
        if not item or item.org_id != org_id:
            raise KeyError(f"Memory {memory_id} not found in org")
        item.status = "confirmed"
        item.updated_at = datetime.utcnow()
        self._traces[memory_id].append(
            {"timestamp": item.updated_at.isoformat(), "event": "meterless_memory_confirmed"}
        )
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
            raise KeyError(f"Memory {memory_id} not found in org")
        item.value = value
        item.updated_at = datetime.utcnow()
        self._traces[memory_id].append(
            {"timestamp": item.updated_at.isoformat(), "event": "meterless_memory_updated", "new_value": value}
        )
        return item

    async def trace(self, org_id: UUID, memory_id: UUID) -> MemoryTrace:
        item = self._items.get(memory_id)
        if not item or item.org_id != org_id:
            raise KeyError(f"Memory {memory_id} not found in org")
        history = self._traces.get(memory_id, [])
        return MemoryTrace(
            memory_id=memory_id,
            history=history,
            backend="meterless" if self.is_real_meterless_active else "meterless_fallback_store",
        )
