# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel
from .user_response import UserResponse

__all__ = ["WorkspaceResponse", "User"]


class User(BaseModel):
    """User with their role in a workspace."""

    joined_at: datetime

    role: Literal["owner", "collaborator", "guest"]
    """Role of a user within a workspace."""

    user: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    conversation_count: Optional[int] = None

    document_count: Optional[int] = None


class WorkspaceResponse(BaseModel):
    created_at: datetime

    created_by_ext_id: str

    description: Optional[str] = None

    external_id: str

    is_public: bool

    name: str

    updated_at: datetime

    private_conversation_count: Optional[int] = None

    private_document_count: Optional[int] = None

    shared_conversation_count: Optional[int] = None

    shared_document_count: Optional[int] = None

    updated_by_ext_id: Optional[str] = None

    user_files_mb: Optional[float] = None

    users: Optional[List[User]] = None

    wrapped_key: Optional[str] = None
