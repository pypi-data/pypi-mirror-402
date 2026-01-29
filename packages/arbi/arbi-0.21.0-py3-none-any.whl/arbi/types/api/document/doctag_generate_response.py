# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from ...._models import BaseModel

__all__ = ["DoctagGenerateResponse"]


class DoctagGenerateResponse(BaseModel):
    """Response for generate annotations endpoint (202 Accepted).

    Returns the accepted doc and tag IDs that will be processed.
    """

    doc_ext_ids: List[str]
    """Document IDs that will be processed"""

    tag_ext_ids: List[str]
    """Tag IDs that will be processed"""
