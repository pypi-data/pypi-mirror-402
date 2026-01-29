"""
Base HTTP clients for Modulo API.

Two authentication methods are supported:
- API Key authentication (ModuloClient)
- RSA signature authentication (ModuloS2SClient)
"""

from __future__ import annotations

import abc
import base64
import os
import time
import typing as t

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from ._constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    ENV_API_KEY,
    ENV_BASE_URL,
    ENV_PRIVATE_KEY,
    ENV_SERVICE_ID,
    ENVIRONMENTS,
)
from ._exceptions import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    ApiKeyNotProvidedError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    PrivateKeyError,
    PrivateKeyNotProvidedError,
    ProjectIdNotProvidedError,
    RateLimitError,
    ServiceIdNotProvidedError,
    UnprocessableEntityError,
)
from ._types import NOT_GIVEN, Body, Headers, NotGiven, Query, Timeout, is_given

if t.TYPE_CHECKING:
    from typing_extensions import Literal, Self


class BaseClient(abc.ABC):
    """Abstract base HTTP client with common functionality."""

    _project_id: str
    _organization_id: t.Optional[str]
    _base_url: str
    _timeout: float
    _max_retries: int
    _default_headers: dict[str, str]

    def __init__(
        self,
        *,
        project_id: str,
        organization_id: t.Optional[str] = None,
        environment: t.Union["Literal['production', 'staging', 'development', 'local']", NotGiven] = NOT_GIVEN,
        base_url: t.Optional[str] = None,
        timeout: t.Union[float, Timeout, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: t.Optional[t.Mapping[str, str]] = None,
    ) -> None:
        """
        Initialize the base client.

        Args:
            project_id: Project ID to operate on (required).
            organization_id: Organization ID (optional).
            environment: Environment to use ('production', 'staging', 'development', 'local').
            base_url: Override base URL (takes precedence over environment).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            default_headers: Default headers to include in all requests.
        """
        # Project ID (required)
        if not project_id:
            raise ProjectIdNotProvidedError()
        self._project_id = project_id

        # Organization ID (optional)
        self._organization_id = organization_id

        # Base URL
        env_base_url = os.environ.get(ENV_BASE_URL)
        if base_url:
            self._base_url = base_url.rstrip("/")
        elif env_base_url:
            self._base_url = env_base_url.rstrip("/")
        elif is_given(environment):
            self._base_url = ENVIRONMENTS.get(environment, ENVIRONMENTS["production"])
        else:
            self._base_url = ENVIRONMENTS["production"]

        # Timeout and retries
        self._timeout = timeout if is_given(timeout) else DEFAULT_TIMEOUT  # type: ignore
        self._max_retries = max_retries

        # Default headers
        self._default_headers = dict(default_headers) if default_headers else {}

    @abc.abstractmethod
    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for the request."""
        ...

    def _build_headers(
        self,
        extra_headers: t.Optional[Headers] = None,
    ) -> dict[str, str]:
        """Build complete headers for request."""
        headers = {
            **self._default_headers,
            **self._get_auth_headers(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        """Create appropriate error based on status code."""
        if response.status_code == 400:
            return BadRequestError(err_msg, response=response, body=body)
        if response.status_code == 401:
            return AuthenticationError(err_msg, response=response, body=body)
        if response.status_code == 403:
            return PermissionDeniedError(err_msg, response=response, body=body)
        if response.status_code == 404:
            return NotFoundError(err_msg, response=response, body=body)
        if response.status_code == 409:
            return ConflictError(err_msg, response=response, body=body)
        if response.status_code == 422:
            return UnprocessableEntityError(err_msg, response=response, body=body)
        if response.status_code == 429:
            return RateLimitError(err_msg, response=response, body=body)
        if response.status_code >= 500:
            return InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def project_id(self) -> str:
        return self._project_id


# =============================================================================
# API Key Authentication Base Clients
# =============================================================================


class ApiKeyBaseClient(BaseClient):
    """Base client with API key authentication."""

    _api_key: str

    def __init__(
        self,
        *,
        api_key: t.Optional[str] = None,
        project_id: t.Optional[str] = None,
        organization_id: t.Optional[str] = None,
        environment: t.Union["Literal['production', 'staging', 'development', 'local']", NotGiven] = NOT_GIVEN,
        base_url: t.Optional[str] = None,
        timeout: t.Union[float, Timeout, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: t.Optional[t.Mapping[str, str]] = None,
    ) -> None:
        """
        Initialize the API key client.

        Args:
            api_key: API key for authentication. Falls back to MODULO_API_KEY env var.
            project_id: Project ID to operate on. Falls back to MODULO_PROJECT_ID env var.
            organization_id: Organization ID (optional). Falls back to MODULO_ORGANIZATION_ID env var.
            environment: Environment to use ('production', 'staging', 'development', 'local').
            base_url: Override base URL (takes precedence over environment).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            default_headers: Default headers to include in all requests.
        """
        # API Key
        self._api_key = api_key or os.environ.get(ENV_API_KEY, "")
        if not self._api_key:
            raise ApiKeyNotProvidedError()

        super().__init__(
            project_id=project_id,
            organization_id=organization_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

    def _get_auth_headers(self) -> dict[str, str]:
        """Get API key authentication headers."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "BlueMachines-Project": self._project_id,
        }
        if self._organization_id:
            headers["X-Organization-Id"] = self._organization_id
        return headers

    @property
    def api_key(self) -> str:
        return self._api_key


# =============================================================================
# S2S (RSA Signature) Authentication Base Clients
# =============================================================================


class S2SBaseClient(BaseClient):
    """Base client with RSA signature authentication for S2S communication."""

    _service_id: str
    _private_key: RSAPrivateKey

    def __init__(
        self,
        *,
        service_id: t.Optional[str] = None,
        private_key: t.Optional[str] = None,
        private_key_password: t.Optional[bytes] = None,
        project_id: t.Optional[str] = None,
        organization_id: t.Optional[str] = None,
        environment: t.Union["Literal['production', 'staging', 'development', 'local']", NotGiven] = NOT_GIVEN,
        base_url: t.Optional[str] = None,
        timeout: t.Union[float, Timeout, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: t.Optional[t.Mapping[str, str]] = None,
    ) -> None:
        """
        Initialize the S2S client.

        Args:
            service_id: Service identifier (must match DB service_accounts.service_id).
                       Falls back to MODULO_SERVICE_ID env var.
            private_key: RSA private key as a string (PEM format).
                        Falls back to MODULO_PRIVATE_KEY env var.
            private_key_password: Password for encrypted private key (optional).
            project_id: Project ID to operate on. Falls back to MODULO_PROJECT_ID env var.
            organization_id: Organization ID (optional). Falls back to MODULO_ORGANIZATION_ID env var.
            environment: Environment to use ('production', 'staging', 'development', 'local').
            base_url: Override base URL (takes precedence over environment).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            default_headers: Default headers to include in all requests.
        """
        # Service ID
        self._service_id = service_id or os.environ.get(ENV_SERVICE_ID, "")
        if not self._service_id:
            raise ServiceIdNotProvidedError()

        # Load private key (direct content, not path)
        key_content = private_key or os.environ.get(ENV_PRIVATE_KEY, "")
        if key_content:
            self._private_key = self._load_private_key_from_string(
                key_content, private_key_password
            )
        else:
            raise PrivateKeyNotProvidedError()

        super().__init__(
            project_id=project_id,
            organization_id=organization_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

    def _load_private_key_from_string(
        self,
        key_string: str,
        password: t.Optional[bytes] = None,
    ) -> RSAPrivateKey:
        """Load RSA private key from PEM string."""
        try:
            key_data = key_string.encode()
            return t.cast(
                RSAPrivateKey,
                serialization.load_pem_private_key(key_data, password=password),
            )
        except Exception as e:
            raise PrivateKeyError(f"Error loading private key: {e}") from e

    def _sign_request(self) -> tuple[str, str]:
        """
        Generate timestamp and signature for the request.

        Returns:
            Tuple of (timestamp, base64_signature)
        """
        timestamp = str(int(time.time()))
        message = f"{self._service_id}:{timestamp}".encode()

        signature = self._private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        signature_b64 = base64.b64encode(signature).decode()
        return timestamp, signature_b64

    def _get_auth_headers(self) -> dict[str, str]:
        """Get S2S authentication headers with RSA signature."""
        timestamp, signature = self._sign_request()
        headers = {
            "X-Service-Id": self._service_id,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "BlueMachines-Project": self._project_id,
        }
        if self._organization_id:
            headers["X-Organization-Id"] = self._organization_id
        return headers

    @property
    def service_id(self) -> str:
        return self._service_id


# =============================================================================
# Sync HTTP Clients
# =============================================================================


class SyncHTTPClientMixin:
    """Mixin providing synchronous HTTP request methods."""

    _client: httpx.Client
    _base_url: str
    _timeout: float
    _max_retries: int

    def _init_http_client(self) -> None:
        """Initialize the synchronous HTTP client."""
        self._client = httpx.Client(timeout=self._timeout)

    def _build_headers(self, extra_headers: t.Optional[Headers] = None) -> dict[str, str]:
        """Build headers - to be implemented by base class."""
        raise NotImplementedError

    def _make_status_error(self, err_msg: str, *, body: object, response: httpx.Response) -> APIStatusError:
        """Create status error - to be implemented by base class."""
        raise NotImplementedError

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make an HTTP request with authentication."""
        url = f"{self._base_url}{path}"
        req_headers = self._build_headers(headers)

        # Filter out None/NOT_GIVEN values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None and not isinstance(v, NotGiven)}

        # Filter out None/NOT_GIVEN values from json body
        if json and isinstance(json, dict):
            json = {k: v for k, v in json.items() if v is not None and not isinstance(v, NotGiven)}

        retries = 0
        last_exception: t.Optional[Exception] = None

        while retries <= self._max_retries:
            try:
                response = self._client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=req_headers,
                    timeout=timeout or self._timeout,
                )

                if response.is_success:
                    return response

                # Handle error responses
                try:
                    body = response.json()
                except Exception:
                    body = response.text

                err_msg = f"Error response {response.status_code}"
                if isinstance(body, dict) and "message" in body:
                    err_msg = body["message"]
                elif isinstance(body, str):
                    err_msg = body

                raise self._make_status_error(err_msg, body=body, response=response)

            except httpx.TimeoutException as e:
                last_exception = APITimeoutError(f"Request timed out: {e}")
                retries += 1
            except httpx.ConnectError as e:
                last_exception = APIConnectionError(f"Connection error: {e}")
                retries += 1
            except APIStatusError:
                raise
            except Exception as e:
                last_exception = APIConnectionError(f"Request failed: {e}")
                retries += 1

        if last_exception:
            raise last_exception
        raise APIConnectionError("Request failed after retries")

    def _get(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make a GET request."""
        return self._request("GET", path, params=params, headers=headers, timeout=timeout)

    def _post(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make a POST request."""
        return self._request("POST", path, params=params, json=json, headers=headers, timeout=timeout)

    def _patch(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make a PATCH request."""
        return self._request("PATCH", path, params=params, json=json, headers=headers, timeout=timeout)

    def _put(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make a PUT request."""
        return self._request("PUT", path, params=params, json=json, headers=headers, timeout=timeout)

    def _delete(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make a DELETE request."""
        return self._request("DELETE", path, params=params, headers=headers, timeout=timeout)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "Self":
        return self  # type: ignore

    def __exit__(self, *args: t.Any) -> None:
        self.close()


class SyncAPIClient(ApiKeyBaseClient, SyncHTTPClientMixin):
    """Synchronous HTTP client with API key authentication."""

    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self._init_http_client()


class SyncS2SAPIClient(S2SBaseClient, SyncHTTPClientMixin):
    """Synchronous HTTP client with RSA signature authentication."""

    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self._init_http_client()


# =============================================================================
# Async HTTP Clients
# =============================================================================


class AsyncHTTPClientMixin:
    """Mixin providing asynchronous HTTP request methods."""

    _client: httpx.AsyncClient
    _base_url: str
    _timeout: float
    _max_retries: int

    def _init_http_client(self) -> None:
        """Initialize the asynchronous HTTP client."""
        self._client = httpx.AsyncClient(timeout=self._timeout)

    def _build_headers(self, extra_headers: t.Optional[Headers] = None) -> dict[str, str]:
        """Build headers - to be implemented by base class."""
        raise NotImplementedError

    def _make_status_error(self, err_msg: str, *, body: object, response: httpx.Response) -> APIStatusError:
        """Create status error - to be implemented by base class."""
        raise NotImplementedError

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make an async HTTP request with authentication."""
        url = f"{self._base_url}{path}"
        req_headers = self._build_headers(headers)

        # Filter out None/NOT_GIVEN values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None and not isinstance(v, NotGiven)}

        # Filter out None/NOT_GIVEN values from json body
        if json and isinstance(json, dict):
            json = {k: v for k, v in json.items() if v is not None and not isinstance(v, NotGiven)}

        retries = 0
        last_exception: t.Optional[Exception] = None

        while retries <= self._max_retries:
            try:
                response = await self._client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=req_headers,
                    timeout=timeout or self._timeout,
                )

                if response.is_success:
                    return response

                # Handle error responses
                try:
                    body = response.json()
                except Exception:
                    body = response.text

                err_msg = f"Error response {response.status_code}"
                if isinstance(body, dict) and "message" in body:
                    err_msg = body["message"]
                elif isinstance(body, str):
                    err_msg = body

                raise self._make_status_error(err_msg, body=body, response=response)

            except httpx.TimeoutException as e:
                last_exception = APITimeoutError(f"Request timed out: {e}")
                retries += 1
            except httpx.ConnectError as e:
                last_exception = APIConnectionError(f"Connection error: {e}")
                retries += 1
            except APIStatusError:
                raise
            except Exception as e:
                last_exception = APIConnectionError(f"Request failed: {e}")
                retries += 1

        if last_exception:
            raise last_exception
        raise APIConnectionError("Request failed after retries")

    async def _get(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make an async GET request."""
        return await self._request("GET", path, params=params, headers=headers, timeout=timeout)

    async def _post(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make an async POST request."""
        return await self._request("POST", path, params=params, json=json, headers=headers, timeout=timeout)

    async def _patch(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make an async PATCH request."""
        return await self._request("PATCH", path, params=params, json=json, headers=headers, timeout=timeout)

    async def _put(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        json: t.Optional[Body] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make an async PUT request."""
        return await self._request("PUT", path, params=params, json=json, headers=headers, timeout=timeout)

    async def _delete(
        self,
        path: str,
        *,
        params: t.Optional[Query] = None,
        headers: t.Optional[Headers] = None,
        timeout: t.Optional[float] = None,
    ) -> httpx.Response:
        """Make an async DELETE request."""
        return await self._request("DELETE", path, params=params, headers=headers, timeout=timeout)

    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "Self":
        return self  # type: ignore

    async def __aexit__(self, *args: t.Any) -> None:
        await self.close()


class AsyncAPIClient(ApiKeyBaseClient, AsyncHTTPClientMixin):
    """Asynchronous HTTP client with API key authentication."""

    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self._init_http_client()


class AsyncS2SAPIClient(S2SBaseClient, AsyncHTTPClientMixin):
    """Asynchronous HTTP client with RSA signature authentication."""

    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self._init_http_client()
