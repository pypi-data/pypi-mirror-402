# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["TagUpdateParams", "TagType"]


class TagUpdateParams(TypedDict, total=False):
    instruction: Optional[str]

    name: Optional[str]

    parent_ext_id: Optional[str]

    shared: Optional[bool]

    tag_type: Optional[TagType]
    """Tag format configuration stored as JSONB.

    Type-specific fields:

    - select: options (list of choices, can be single or multi-select)
    - search: tag name is the query, chunks include relevance scores
    - checkbox, text, number, folder: type only
    """

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]


class TagType(TypedDict, total=False):
    """Tag format configuration stored as JSONB.

    Type-specific fields:
    - select: options (list of choices, can be single or multi-select)
    - search: tag name is the query, chunks include relevance scores
    - checkbox, text, number, folder: type only
    """

    options: SequenceNotStr[str]

    type: Literal["checkbox", "text", "number", "select", "folder", "search", "date"]
