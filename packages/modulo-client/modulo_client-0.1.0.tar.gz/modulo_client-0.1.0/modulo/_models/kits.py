"""
Type definitions for Integration Kits.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class KitAuthScheme(TypedDict, total=False):
    """Kit auth scheme info."""
    id: str
    name: str
    auth_scheme: str
    secret_id: str
    config: dict[str, Any]
    status: str


class Kit(TypedDict, total=False):
    """Integration Kit object."""
    id: str
    project_id: str
    organization_id: Optional[str]
    slug: str
    name: str
    description: str
    integration_id: str
    auth_scheme: KitAuthScheme
    status: str
    tags: list[str]
    created_at: str
    updated_at: str


class KitListData(TypedDict):
    """Data field for list kits response."""
    content: list[Kit]
    total: int
    page: int
    size: int


class KitListResponse(TypedDict, total=False):
    """Response from list kits."""
    status: str
    message: str
    data: KitListData
    traceback: Optional[str]
    code: int


class KitRetrieveResponse(TypedDict, total=False):
    """Response from retrieve kit."""
    status: str
    message: str
    data: Kit
    traceback: Optional[str]
    code: int
