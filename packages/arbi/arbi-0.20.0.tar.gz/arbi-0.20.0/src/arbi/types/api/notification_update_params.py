# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Required, TypedDict

__all__ = ["NotificationUpdateParams", "Update"]


class NotificationUpdateParams(TypedDict, total=False):
    updates: Required[Iterable[Update]]


class Update(TypedDict, total=False):
    """Single notification update for bulk PATCH.

    Supports two operations:
    - content: Re-encrypt content (key rotation)
    - read: Mark as read (only recipient can do this)
    """

    external_id: Required[str]

    content: Optional[str]

    read: Optional[bool]
