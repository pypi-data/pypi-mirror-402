"""
Main Modulo client classes.

Two client types are available:
- ModuloClient: Uses API key authentication (api_key + project_id)
- ModuloS2SClient: Uses RSA signature authentication (service_id + private_key)
"""

from __future__ import annotations

import typing as t

from ._base_client import (
    AsyncAPIClient,
    AsyncS2SAPIClient,
    SyncAPIClient,
    SyncS2SAPIClient,
)
from ._constants import DEFAULT_MAX_RETRIES, ENVIRONMENTS
from ._types import NOT_GIVEN, NotGiven, Timeout
from .base.actions import ActionsResource, AsyncActionsResource
from .base.integrations import AsyncIntegrationsResource, IntegrationsResource
from .base.kits import AsyncKitsResource, KitsResource

if t.TYPE_CHECKING:
    from typing_extensions import Literal, Self


__all__ = [
    "ModuloClient",
    "AsyncModuloClient",
    "ModuloS2SClient",
    "AsyncModuloS2SClient",
    "ENVIRONMENTS",
]


# =============================================================================
# API Key Authentication Clients
# =============================================================================


class ModuloClient(SyncAPIClient):
    """
    Synchronous Modulo client with API key authentication.

    Example:
        ```python
        from modulo import ModuloClient

        client = ModuloClient(
            api_key="your-api-key",
            project_id="project-123",
        )

        # List kits
        kits = client.kits.list()

        # Execute an action
        result = client.actions.execute(
            kit_id="kit-123",
            action_id="action-456",
            arguments={"title": "Bug report"},
        )
        ```
    """

    integrations: IntegrationsResource
    kits: KitsResource
    actions: ActionsResource

    def __init__(
        self,
        *,
        api_key: str | None = None,
        project_id: str,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | NotGiven = NOT_GIVEN,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: t.Mapping[str, str] | None = None,
    ) -> None:
        """
        Initialize the Modulo client.

        Args:
            api_key: API key for authentication. Falls back to MODULO_API_KEY env var.
            project_id: Project ID to operate on (required).
            organization_id: Organization ID (optional).
            environment: Environment to use ('production', 'staging', 'development', 'local').
            base_url: Override base URL (takes precedence over environment).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            default_headers: Default headers to include in all requests.
        """
        super().__init__(
            api_key=api_key,
            project_id=project_id,
            organization_id=organization_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

        # Initialize resources
        self.integrations = IntegrationsResource(self)
        self.kits = KitsResource(self)
        self.actions = ActionsResource(self)

    def copy(
        self,
        *,
        api_key: str | None = None,
        project_id: str | None = None,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int | None = None,
    ) -> Self:
        """Create a new client instance with optional overrides."""
        return self.__class__(
            api_key=api_key or self._api_key,
            project_id=project_id or self._project_id,
            organization_id=organization_id or self._organization_id,
            environment=environment if environment else NOT_GIVEN,
            base_url=base_url or self._base_url,
            timeout=timeout if not isinstance(timeout, NotGiven) else self._timeout,
            max_retries=max_retries if max_retries is not None else self._max_retries,
        )

    with_options = copy


class AsyncModuloClient(AsyncAPIClient):
    """
    Asynchronous Modulo client with API key authentication.

    Example:
        ```python
        from modulo import AsyncModuloClient

        async with AsyncModuloClient(
            api_key="your-api-key",
            project_id="project-123",
        ) as client:
            # List kits
            kits = await client.kits.list()

            # Execute an action
            result = await client.actions.execute(
                kit_id="kit-123",
                action_id="action-456",
                arguments={"title": "Bug report"},
            )
        ```
    """

    integrations: AsyncIntegrationsResource
    kits: AsyncKitsResource
    actions: AsyncActionsResource

    def __init__(
        self,
        *,
        api_key: str | None = None,
        project_id: str,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | NotGiven = NOT_GIVEN,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: t.Mapping[str, str] | None = None,
    ) -> None:
        """
        Initialize the async Modulo client.

        Args:
            api_key: API key for authentication. Falls back to MODULO_API_KEY env var.
            project_id: Project ID to operate on (required).
            organization_id: Organization ID (optional).
            environment: Environment to use ('production', 'staging', 'development', 'local').
            base_url: Override base URL (takes precedence over environment).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            default_headers: Default headers to include in all requests.
        """
        super().__init__(
            api_key=api_key,
            project_id=project_id,
            organization_id=organization_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

        # Initialize resources
        self.integrations = AsyncIntegrationsResource(self)
        self.kits = AsyncKitsResource(self)
        self.actions = AsyncActionsResource(self)

    def copy(
        self,
        *,
        api_key: str | None = None,
        project_id: str | None = None,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int | None = None,
    ) -> Self:
        """Create a new client instance with optional overrides."""
        return self.__class__(
            api_key=api_key or self._api_key,
            project_id=project_id or self._project_id,
            organization_id=organization_id or self._organization_id,
            environment=environment if environment else NOT_GIVEN,
            base_url=base_url or self._base_url,
            timeout=timeout if not isinstance(timeout, NotGiven) else self._timeout,
            max_retries=max_retries if max_retries is not None else self._max_retries,
        )

    with_options = copy


# =============================================================================
# S2S (RSA Signature) Authentication Clients
# =============================================================================


class ModuloS2SClient(SyncS2SAPIClient):
    """
    Synchronous Modulo client with RSA signature authentication for S2S communication.

    Used by LiveKit agent workers to authenticate via private key signature.

    Example:
        ```python
        from modulo import ModuloS2SClient

        client = ModuloS2SClient(
            service_id="my-livekit-service",
            private_key="-----BEGIN PRIVATE KEY-----\\n...",
            project_id="project-123",
        )

        # List kits
        kits = client.kits.list()

        # Execute an action
        result = client.actions.execute(
            kit_id="kit-123",
            action_id="action-456",
            arguments={"title": "Bug report"},
        )
        ```
    """

    integrations: IntegrationsResource
    kits: KitsResource
    actions: ActionsResource

    def __init__(
        self,
        *,
        service_id: str | None = None,
        private_key: str | None = None,
        private_key_password: bytes | None = None,
        project_id: str,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | NotGiven = NOT_GIVEN,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: t.Mapping[str, str] | None = None,
    ) -> None:
        """
        Initialize the S2S Modulo client.

        Args:
            service_id: Service identifier (must match DB service_accounts.service_id).
                       Falls back to MODULO_SERVICE_ID env var.
            private_key: RSA private key as a string (PEM format).
                        Falls back to MODULO_PRIVATE_KEY env var.
            private_key_password: Password for encrypted private key (optional).
            project_id: Project ID to operate on (required).
            organization_id: Organization ID (optional).
            environment: Environment to use ('production', 'staging', 'development', 'local').
            base_url: Override base URL (takes precedence over environment).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            default_headers: Default headers to include in all requests.
        """
        super().__init__(
            service_id=service_id,
            private_key=private_key,
            private_key_password=private_key_password,
            project_id=project_id,
            organization_id=organization_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

        # Initialize resources
        self.integrations = IntegrationsResource(self)
        self.kits = KitsResource(self)
        self.actions = ActionsResource(self)

    def copy(
        self,
        *,
        service_id: str | None = None,
        private_key: str | None = None,
        project_id: str | None = None,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int | None = None,
    ) -> Self:
        """Create a new client instance with optional overrides."""
        return self.__class__(
            service_id=service_id or self._service_id,
            private_key=private_key,
            project_id=project_id or self._project_id,
            organization_id=organization_id or self._organization_id,
            environment=environment if environment else NOT_GIVEN,
            base_url=base_url or self._base_url,
            timeout=timeout if not isinstance(timeout, NotGiven) else self._timeout,
            max_retries=max_retries if max_retries is not None else self._max_retries,
        )

    with_options = copy


class AsyncModuloS2SClient(AsyncS2SAPIClient):
    """
    Asynchronous Modulo client with RSA signature authentication for S2S communication.

    Used by LiveKit agent workers to authenticate via private key signature.

    Example:
        ```python
        from modulo import AsyncModuloS2SClient

        async with AsyncModuloS2SClient(
            service_id="my-livekit-service",
            private_key="-----BEGIN PRIVATE KEY-----\\n...",
            project_id="project-123",
        ) as client:
            # List kits
            kits = await client.kits.list()

            # Execute an action
            result = await client.actions.execute(
                kit_id="kit-123",
                action_id="action-456",
                arguments={"title": "Bug report"},
            )
        ```
    """

    integrations: AsyncIntegrationsResource
    kits: AsyncKitsResource
    actions: AsyncActionsResource

    def __init__(
        self,
        *,
        service_id: str | None = None,
        private_key: str | None = None,
        private_key_password: bytes | None = None,
        project_id: str,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | NotGiven = NOT_GIVEN,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: t.Mapping[str, str] | None = None,
    ) -> None:
        """
        Initialize the async S2S Modulo client.

        Args:
            service_id: Service identifier (must match DB service_accounts.service_id).
                       Falls back to MODULO_SERVICE_ID env var.
            private_key: RSA private key as a string (PEM format).
                        Falls back to MODULO_PRIVATE_KEY env var.
            private_key_password: Password for encrypted private key (optional).
            project_id: Project ID to operate on (required).
            organization_id: Organization ID (optional).
            environment: Environment to use ('production', 'staging', 'development', 'local').
            base_url: Override base URL (takes precedence over environment).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            default_headers: Default headers to include in all requests.
        """
        super().__init__(
            service_id=service_id,
            private_key=private_key,
            private_key_password=private_key_password,
            project_id=project_id,
            organization_id=organization_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

        # Initialize resources
        self.integrations = AsyncIntegrationsResource(self)
        self.kits = AsyncKitsResource(self)
        self.actions = AsyncActionsResource(self)

    def copy(
        self,
        *,
        service_id: str | None = None,
        private_key: str | None = None,
        project_id: str | None = None,
        organization_id: str | None = None,
        environment: Literal["production", "staging", "development", "local"] | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | NotGiven = NOT_GIVEN,
        max_retries: int | None = None,
    ) -> Self:
        """Create a new client instance with optional overrides."""
        return self.__class__(
            service_id=service_id or self._service_id,
            private_key=private_key,
            project_id=project_id or self._project_id,
            organization_id=organization_id or self._organization_id,
            environment=environment if environment else NOT_GIVEN,
            base_url=base_url or self._base_url,
            timeout=timeout if not isinstance(timeout, NotGiven) else self._timeout,
            max_retries=max_retries if max_retries is not None else self._max_retries,
        )

    with_options = copy


# Aliases for backward compatibility
Client = ModuloClient
AsyncClient = AsyncModuloClient
