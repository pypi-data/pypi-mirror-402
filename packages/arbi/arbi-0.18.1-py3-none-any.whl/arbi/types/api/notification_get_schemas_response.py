# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel
from .user_response import UserResponse

__all__ = [
    "NotificationGetSchemasResponse",
    "ClientMessage",
    "ServerMessage",
    "ServerMessageAuthResultMessage",
    "ServerMessageConnectionClosedMessage",
    "ServerMessagePresenceUpdateMessage",
    "ServerMessageErrorMessage",
    "ServerMessageTaskUpdateMessage",
    "ServerMessageUserMessageNotification",
    "ServerMessageWorkspaceShareNotification",
    "ServerMessageContactAcceptedNotification",
]


class ClientMessage(BaseModel):
    """Client authentication message."""

    token: str

    type: Optional[Literal["auth"]] = None


class ServerMessageAuthResultMessage(BaseModel):
    """Server response to authentication."""

    success: bool

    reason: Optional[str] = None

    type: Optional[Literal["auth_result"]] = None


class ServerMessageConnectionClosedMessage(BaseModel):
    """Sent when connection is closed (e.g., another tab opened)."""

    message: str

    type: Optional[Literal["connection_closed"]] = None


class ServerMessagePresenceUpdateMessage(BaseModel):
    """Sent when a contact's online status changes or is no longer tracked."""

    status: Literal["online", "unknown"]

    timestamp: str

    user_id: str

    type: Optional[Literal["presence_update"]] = None


class ServerMessageErrorMessage(BaseModel):
    """Sent when server fails to process a client message."""

    message: str

    type: Optional[Literal["error"]] = None


class ServerMessageTaskUpdateMessage(BaseModel):
    """Document processing progress update."""

    doc_ext_id: str

    file_name: str

    progress: int

    status: Literal["queued", "processing", "completed", "failed"]

    workspace_ext_id: str

    type: Optional[Literal["task_update"]] = None


class ServerMessageUserMessageNotification(BaseModel):
    """E2E encrypted message (bilateral).

    One row, both parties see it via RLS.
    Client: sender == me → I sent it, else I received it.
    """

    content: str

    created_at: datetime

    external_id: str

    new: bool

    recipient: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    sender: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    updated_at: datetime

    type: Optional[Literal["user_message"]] = None


class ServerMessageWorkspaceShareNotification(BaseModel):
    """Workspace shared (bilateral).

    One row, both parties see it via RLS.
    """

    created_at: datetime

    external_id: str

    new: bool

    recipient: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    sender: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    updated_at: datetime

    workspace_ext_id: str

    type: Optional[Literal["workspace_share"]] = None


class ServerMessageContactAcceptedNotification(BaseModel):
    """Contact invitation accepted.

    Sent to inviter when their invited contact registers.
    sender = new user who registered, recipient = inviter.
    """

    created_at: datetime

    external_id: str

    new: bool

    recipient: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    sender: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    updated_at: datetime

    type: Optional[Literal["contact_accepted"]] = None


ServerMessage: TypeAlias = Union[
    ServerMessageAuthResultMessage,
    ServerMessageConnectionClosedMessage,
    ServerMessagePresenceUpdateMessage,
    ServerMessageErrorMessage,
    ServerMessageTaskUpdateMessage,
    ServerMessageUserMessageNotification,
    ServerMessageWorkspaceShareNotification,
    ServerMessageContactAcceptedNotification,
]


class NotificationGetSchemasResponse(BaseModel):
    """Container for all WebSocket message schemas."""

    client_messages: Optional[List[ClientMessage]] = None

    server_messages: Optional[List[ServerMessage]] = None
