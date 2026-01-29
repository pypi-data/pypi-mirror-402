# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

__all__ = ["WorkspaceRemoveUsersParams", "User"]


class WorkspaceRemoveUsersParams(TypedDict, total=False):
    users: Required[Iterable[User]]


class User(TypedDict, total=False):
    """A user to remove from a workspace."""

    user_ext_id: Required[str]
