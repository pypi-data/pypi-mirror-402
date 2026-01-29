"""
Common response types for Modulo API.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class RequestInfo(TypedDict, total=False):
    """Request info in API response."""
    id: str
    idempotency_key: Optional[str]
    project_id: str


class PaginatedContent(TypedDict, total=False):
    """Paginated content wrapper."""
    content: list[Any]
    total: int
    page: int
    size: int


class APIResponse(TypedDict, total=False):
    """Base API response structure."""
    status: str
    message: str
    data: Any
    traceback: Optional[str]
    code: int
    request: RequestInfo
