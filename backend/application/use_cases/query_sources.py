"""
Application Use Case: Query Grounded Vendor Knowledge Sources
Retrieves indexed vendor manuals, TAC documentation chunks, and source URLs.
"""

from typing import Any, Dict, List, Optional

from backend.application.ports.vector_repository import IVectorRepository


class QueryVendorSourcesUseCase:
    """Use case for querying indexed vendor documentation sources."""

    def __init__(self, vector_repo: IVectorRepository) -> None:
        self._vector_repo = vector_repo

    async def execute(
        self,
        vendor: Optional[str] = None,
        protocol: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Query documentation sources for a vendor or protocol."""
        query_text = f"{vendor or ''} {protocol or ''} network troubleshooting configuration".strip()
        docs = await self._vector_repo.find_relevant_docs(
            query_text=query_text,
            limit=limit,
            vendor=vendor,
            protocol=protocol,
        )
        return docs
