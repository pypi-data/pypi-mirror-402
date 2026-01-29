# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel

__all__ = ["WorkspaceShareResponse"]


class WorkspaceShareResponse(BaseModel):
    detail: str

    shared_with: str

    workspace_ext_id: str
