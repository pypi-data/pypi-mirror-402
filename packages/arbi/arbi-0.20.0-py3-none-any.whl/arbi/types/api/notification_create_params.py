# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

__all__ = ["NotificationCreateParams", "Message"]


class NotificationCreateParams(TypedDict, total=False):
    messages: Required[Iterable[Message]]


class Message(TypedDict, total=False):
    """Single recipient for bulk message send."""

    content: Required[str]

    recipient_ext_id: Required[str]
