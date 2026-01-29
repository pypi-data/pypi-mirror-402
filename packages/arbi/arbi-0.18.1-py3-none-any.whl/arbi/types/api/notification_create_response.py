# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from ..._models import BaseModel
from .user_response import UserResponse

__all__ = ["NotificationCreateResponse", "NotificationCreateResponseItem"]


class NotificationCreateResponseItem(BaseModel):
    """Notification response model for API and WebSocket.

    Bilateral: both sender and recipient see the same row.
    Client determines perspective: sender == me → I sent it, else I received it.
    """

    created_at: datetime

    external_id: str

    recipient: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    sender: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    type: str

    updated_at: datetime

    content: Optional[str] = None

    new: Optional[bool] = None

    workspace_ext_id: Optional[str] = None


NotificationCreateResponse: TypeAlias = List[NotificationCreateResponseItem]
