# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel
from .user_response import UserResponse

__all__ = ["WorkspaceGetUsersResponse", "WorkspaceGetUsersResponseItem"]


class WorkspaceGetUsersResponseItem(BaseModel):
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


WorkspaceGetUsersResponse: TypeAlias = List[WorkspaceGetUsersResponseItem]
