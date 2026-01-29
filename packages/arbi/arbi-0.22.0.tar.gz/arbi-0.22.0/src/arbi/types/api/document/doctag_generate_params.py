# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = ["DoctagGenerateParams"]


class DoctagGenerateParams(TypedDict, total=False):
    doc_ext_ids: Required[SequenceNotStr[str]]

    tag_ext_ids: Required[SequenceNotStr[str]]

    config_ext_id: Optional[str]
    """Configuration to use for LLM"""

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
