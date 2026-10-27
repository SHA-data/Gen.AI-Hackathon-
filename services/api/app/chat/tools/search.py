"""Web search tool wrapper (Part A6, Part B2)."""
from typing import Any, Dict, List
from uuid import uuid4
from pydantic import BaseModel

from packages.contracts.envelope import ToolResultEnvelope
from packages.contracts.search import FakeSearchProvider, SearchProvider
from services.api.app.core.auth import AuthContext

_search_provider: SearchProvider = FakeSearchProvider()

class WebSearchArgs(BaseModel):
    query: str
    max_results: int = 3

async def handle_web_search(auth: AuthContext, query: str, max_results: int = 3) -> ToolResultEnvelope[List[Dict[str, Any]]]:
    results = await _search_provider.search(query, max_results=max_results)
    return ToolResultEnvelope(
        status="ok",
        data=[r.model_dump() for r in results],
        sources=[],
        warnings=["Web content is external and untrusted; context only."],
        run_id=uuid4(),
    )
