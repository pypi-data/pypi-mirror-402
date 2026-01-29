# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime

from ...._models import BaseModel

__all__ = ["DocTagResponse", "Citations"]


class Citations(BaseModel):
    """Data for a single citation - shared by DocTags and ModelCitationTool."""

    chunk_ids: List[str]

    offset_end: int

    offset_start: int

    statement: str


class DocTagResponse(BaseModel):
    """Response for doctag operations - the link between a document and a tag."""

    created_at: datetime

    created_by_ext_id: str

    doc_ext_id: str

    tag_ext_id: str

    updated_at: datetime

    citations: Optional[Dict[str, Citations]] = None

    note: Optional[str] = None

    updated_by_ext_id: Optional[str] = None
