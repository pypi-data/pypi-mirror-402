"""
Type definitions for Integrations.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class CredentialProperty(TypedDict, total=False):
    """Credential property definition."""
    type: str
    title: str
    description: Optional[str]
    default: Optional[Any]
    location: Optional[str]
    enum: Optional[list[str]]


class Credentials(TypedDict, total=False):
    """Credentials schema."""
    properties: dict[str, CredentialProperty]
    required: list[str]


class AuthScheme(TypedDict, total=False):
    """Auth scheme definition."""
    type: str
    credentials: Credentials
    config: Optional[dict[str, Any]]


class Integration(TypedDict, total=False):
    """Integration object."""
    id: str
    project_id: str
    organization_id: Optional[str]
    name: str
    slug: str
    category: list[str]
    description: str
    status: str
    auth_schemes: dict[str, AuthScheme]
    config: dict[str, Any]
    icon_url: Optional[str]
    documentation_url: Optional[str]
    tags: list[str]
    created_at: str
    updated_at: str


class IntegrationListData(TypedDict):
    """Data field for list integrations response."""
    content: list[Integration]
    total: int
    page: int
    size: int


class IntegrationListResponse(TypedDict, total=False):
    """Response from list integrations."""
    status: str
    message: str
    data: IntegrationListData
    traceback: Optional[str]
    code: int


class IntegrationRetrieveResponse(TypedDict, total=False):
    """Response from retrieve integration."""
    status: str
    message: str
    data: Integration
    traceback: Optional[str]
    code: int
