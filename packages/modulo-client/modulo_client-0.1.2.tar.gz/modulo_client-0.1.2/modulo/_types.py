"""
Type definitions for the Modulo client.
"""

from collections.abc import Mapping
from typing import Any, TypedDict

import httpx


class _Omit:
    """Sentinel class to indicate that a value should be omitted."""

    _instance: "_Omit | None" = None

    def __new__(cls) -> "_Omit":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "OMIT"

    def __bool__(self) -> bool:
        return False


OMIT = _Omit()
Omit = _Omit | Any


class NotGiven:
    """Sentinel class to indicate that a parameter was not provided."""

    _instance: "NotGiven | None" = None

    def __new__(cls) -> "NotGiven":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "NOT_GIVEN"

    def __bool__(self) -> bool:
        return False


NOT_GIVEN = NotGiven()

# Type aliases
Headers = Mapping[str, str]
Query = Mapping[str, object]
Body = object | None

# Timeout types
Timeout = float | httpx.Timeout | None

# Transport types
Transport = httpx.BaseTransport
ProxiesTypes = str | httpx.URL | httpx.Proxy


class RequestOptions(TypedDict, total=False):
    """Options that can be passed to individual API requests."""

    headers: Headers
    params: Query
    timeout: Timeout
    max_retries: int


def is_given(value: Any) -> bool:
    """Check if a value was explicitly provided (not NOT_GIVEN)."""
    return not isinstance(value, NotGiven)


def omit_if_not_given(value: Any) -> Any:
    """Return OMIT if value is NOT_GIVEN, otherwise return the value."""
    return OMIT if isinstance(value, NotGiven) else value
