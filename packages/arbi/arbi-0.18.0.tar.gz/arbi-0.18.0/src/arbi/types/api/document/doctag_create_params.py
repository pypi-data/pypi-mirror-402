# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = ["DoctagCreateParams", "Citations"]


class DoctagCreateParams(TypedDict, total=False):
    doc_ext_ids: Required[SequenceNotStr[str]]

    tag_ext_id: Required[str]

    citations: Optional[Dict[str, Citations]]

    note: Optional[str]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]


class Citations(TypedDict, total=False):
    """Data for a single citation - shared by DocTags and ModelCitationTool."""

    chunk_ids: Required[SequenceNotStr[str]]

    offset_end: Required[int]

    offset_start: Required[int]

    statement: Required[str]
