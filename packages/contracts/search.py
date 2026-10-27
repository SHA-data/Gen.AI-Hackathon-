"""Search Provider protocol and Fake implementation."""
from datetime import date
from typing import List, Protocol
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    retrieved_date: date = Field(default_factory=date.today)
    is_untrusted: bool = True

class SearchProvider(Protocol):
    """Protocol for web search (context only)."""
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        ...

class FakeSearchProvider:
    """Fake search provider for testing context retrieval."""
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        return [
            SearchResult(
                url="https://market-insights.synthetic/benchmarks/2026",
                title="B2B Agency Billing Benchmarks 2026",
                snippet="Average payment terms expanded from 34 days to 46 days in 2026, leading to increased demand for retainers.",
                retrieved_date=date.today(),
                is_untrusted=True,
            )
        ]
