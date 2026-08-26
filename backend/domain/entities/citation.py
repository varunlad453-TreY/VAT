"""
Domain Entity: Knowledge Chunk & Vendor Documentation Citation
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class VendorDocCitation(BaseModel):
    """Grounded vendor manual citation entity."""
    source_url: str = Field(..., description="Official vendor documentation URL")
    title: str = Field(..., description="Document manual title")
    vendor: str = Field(default="cisco", description="Hardware/software vendor")
    similarity_score: float = Field(..., description="Cosine / Hybrid similarity score (0.0 to 1.0)")
    excerpt: str = Field(..., description="Relevant knowledge snippet from vendor manual")


class KnowledgeChunk(BaseModel):
    """Raw chunk of vendor technical documentation for vectorization."""
    id: Optional[int] = None
    source_url: str
    title: str
    vendor: str
    product_family: str = "routing"
    protocol: str = "general"
    error_codes: List[str] = Field(default_factory=list)
    chunk_text: str
    embedding: Optional[List[float]] = None
