# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

from ..._types import SequenceNotStr

__all__ = ["WorkspaceUpdateUserRolesParams"]


class WorkspaceUpdateUserRolesParams(TypedDict, total=False):
    role: Required[Literal["owner", "collaborator", "guest"]]
    """Role of a user within a workspace."""

    user_ext_ids: Required[SequenceNotStr[str]]
