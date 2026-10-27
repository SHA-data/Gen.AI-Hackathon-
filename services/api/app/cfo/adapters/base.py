from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID


class FinanceDataSource(ABC):
    """Abstract interface for external finance data sources (CSV, PostgreSQL, Zetaris)."""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection or verify health of data source."""
        pass

    @abstractmethod
    async def query_transactions(
        self,
        org_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Query historical transactions."""
        pass

    @abstractmethod
    async def query_invoices(self, org_id: UUID) -> List[Dict[str, Any]]:
        """Query receivables and payables."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Diagnostic health status of data source."""
        pass
