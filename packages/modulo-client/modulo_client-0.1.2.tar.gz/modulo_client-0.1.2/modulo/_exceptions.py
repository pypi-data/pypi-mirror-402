"""
Modulo client exceptions.
"""

from __future__ import annotations

import typing as t

import httpx


class ModuloError(Exception):
    """Base class for all Modulo client errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(ModuloError):
    """Raised when the client is not properly configured."""

    pass


class ApiKeyNotProvidedError(ConfigurationError):
    """Raised when API key is required but not provided."""

    def __init__(self) -> None:
        super().__init__(
            "API key not provided. Either provide api_key parameter "
            "or set MODULO_API_KEY environment variable."
        )


class ServiceIdNotProvidedError(ConfigurationError):
    """Raised when service ID is required but not provided."""

    def __init__(self) -> None:
        super().__init__(
            "Service ID not provided. Either provide service_id parameter "
            "or set MODULO_SERVICE_ID environment variable."
        )


class PrivateKeyNotProvidedError(ConfigurationError):
    """Raised when private key is required but not provided."""

    def __init__(self) -> None:
        super().__init__(
            "Private key not provided. Either provide private_key parameter "
            "or set MODULO_PRIVATE_KEY environment variable."
        )


class ProjectIdNotProvidedError(ConfigurationError):
    """Raised when project ID is required but not provided."""

    def __init__(self) -> None:
        super().__init__(
            "Project ID not provided. The project_id parameter is required."
        )


class PrivateKeyError(ConfigurationError):
    """Raised when there's an error loading or using the private key."""

    pass


class APIError(ModuloError):
    """Base class for API errors."""

    def __init__(
        self,
        message: str,
        *,
        response: t.Optional[httpx.Response] = None,
        body: t.Optional[object] = None,
    ) -> None:
        super().__init__(message)
        self.response = response
        self.body = body
        self.status_code = response.status_code if response else None

    @property
    def request_id(self) -> t.Optional[str]:
        if self.response is not None:
            return self.response.headers.get("x-request-id")
        return None


class APIStatusError(APIError):
    """Raised when the API returns an error status code."""

    pass


class BadRequestError(APIStatusError):
    """400 Bad Request."""

    pass


class AuthenticationError(APIStatusError):
    """401 Unauthorized."""

    pass


class PermissionDeniedError(APIStatusError):
    """403 Forbidden."""

    pass


class NotFoundError(APIStatusError):
    """404 Not Found."""

    pass


class ConflictError(APIStatusError):
    """409 Conflict."""

    pass


class UnprocessableEntityError(APIStatusError):
    """422 Unprocessable Entity."""

    pass


class RateLimitError(APIStatusError):
    """429 Too Many Requests."""

    pass


class InternalServerError(APIStatusError):
    """500+ Server Error."""

    pass


class APIConnectionError(APIError):
    """Raised when there's a connection error."""

    def __init__(self, message: str = "Connection error") -> None:
        super().__init__(message)


class APITimeoutError(APIConnectionError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)


class APIResponseValidationError(APIError):
    """Raised when the API response doesn't match the expected schema."""

    pass
