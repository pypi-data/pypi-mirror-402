# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["WorkspaceAddUsersParams"]


class WorkspaceAddUsersParams(TypedDict, total=False):
    emails: Required[SequenceNotStr[str]]

    role: Literal["owner", "collaborator", "guest"]
    """Role of a user within a workspace."""

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
