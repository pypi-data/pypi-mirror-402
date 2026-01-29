# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel
from .user_response import UserResponse

__all__ = [
    "NotificationGetSchemasResponse",
    "ClientMessage",
    "ClientMessageAuthMessage",
    "ClientMessageSendMessageRequestOutput",
    "ServerMessage",
    "ServerMessageAuthResultMessage",
    "ServerMessageConnectionClosedMessage",
    "ServerMessagePresenceUpdateMessage",
    "ServerMessageErrorMessage",
    "ServerMessageTaskUpdateMessage",
    "ServerMessageBatchCompleteMessage",
    "ServerMessageNotificationResponse",
]


class ClientMessageAuthMessage(BaseModel):
    """Client authentication message."""

    token: str

    type: Optional[Literal["auth"]] = None


class ClientMessageSendMessageRequestOutput(BaseModel):
    """Client request to send an encrypted message."""

    encrypted_content: str

    recipient: str

    type: Optional[Literal["send_message"]] = None


ClientMessage: TypeAlias = Union[ClientMessageAuthMessage, ClientMessageSendMessageRequestOutput]


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

    status: Literal["queued", "parsing", "encrypting", "indexing", "analysing", "completed", "failed"]

    workspace_ext_id: str

    type: Optional[Literal["task_update"]] = None


class ServerMessageBatchCompleteMessage(BaseModel):
    """Notification that a batch operation (upload or doctag generation) completed."""

    batch_type: Literal["upload", "doctag_generate"]

    doc_ext_ids: List[str]

    workspace_ext_id: str

    type: Optional[Literal["batch_complete"]] = None


class ServerMessageNotificationResponse(BaseModel):
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

    type: Literal[
        "user_message",
        "workspaceuser_added_owner",
        "workspaceuser_added_collaborator",
        "workspaceuser_added_guest",
        "workspaceuser_removed",
        "workspaceuser_updated_owner",
        "workspaceuser_updated_collaborator",
        "workspaceuser_updated_guest",
        "contact_accepted",
    ]
    """Notification types - all persisted AND delivered via WebSocket.

    Type is self-descriptive, no need to parse content field.
    """

    updated_at: datetime

    content: Optional[str] = None

    new: Optional[bool] = None

    workspace_ext_id: Optional[str] = None


ServerMessage: TypeAlias = Union[
    ServerMessageAuthResultMessage,
    ServerMessageConnectionClosedMessage,
    ServerMessagePresenceUpdateMessage,
    ServerMessageErrorMessage,
    ServerMessageTaskUpdateMessage,
    ServerMessageBatchCompleteMessage,
    ServerMessageNotificationResponse,
]


class NotificationGetSchemasResponse(BaseModel):
    """Container for all WebSocket message schemas."""

    client_messages: Optional[List[ClientMessage]] = None

    server_messages: Optional[List[ServerMessage]] = None
