"""
Integrations resource for Modulo API.
"""

from __future__ import annotations

import typing as t

from .._models.integrations import (
    IntegrationListResponse,
    IntegrationRetrieveResponse,
)
from .._types import NOT_GIVEN, NotGiven

if t.TYPE_CHECKING:
    from .._base_client import SyncAPIClient, AsyncAPIClient, SyncS2SAPIClient, AsyncS2SAPIClient


class IntegrationsResource:
    """Resource for managing integrations."""

    _client: t.Union["SyncAPIClient", "SyncS2SAPIClient"]

    def __init__(self, client: t.Union["SyncAPIClient", "SyncS2SAPIClient"]) -> None:
        self._client = client

    def list(
        self,
        *,
        page: int | NotGiven = NOT_GIVEN,
        size: int | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
    ) -> IntegrationListResponse:
        """
        List all integrations.

        Args:
            page: Page number (default: 1).
            size: Items per page (default: 50).
            status: Filter by status.

        Returns:
            List of integrations.
        """
        response = self._client._get(
            "/api/v1/integrations",
            params={
                "page": page,
                "size": size,
                "status": status,
            },
        )
        return response.json()

    def retrieve(self, integration_id: str) -> IntegrationRetrieveResponse:
        """
        Retrieve a specific integration.

        Args:
            integration_id: The integration ID.

        Returns:
            Integration details.
        """
        response = self._client._get(f"/api/v1/integrations/{integration_id}")
        return response.json()


class AsyncIntegrationsResource:
    """Async resource for managing integrations."""

    _client: t.Union["AsyncAPIClient", "AsyncS2SAPIClient"]

    def __init__(self, client: t.Union["AsyncAPIClient", "AsyncS2SAPIClient"]) -> None:
        self._client = client

    async def list(
        self,
        *,
        page: int | NotGiven = NOT_GIVEN,
        size: int | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
    ) -> IntegrationListResponse:
        """
        List all integrations.

        Args:
            page: Page number (default: 1).
            size: Items per page (default: 50).
            status: Filter by status.

        Returns:
            List of integrations.
        """
        response = await self._client._get(
            "/api/v1/integrations",
            params={
                "page": page,
                "size": size,
                "status": status,
            },
        )
        return response.json()

    async def retrieve(self, integration_id: str) -> IntegrationRetrieveResponse:
        """
        Retrieve a specific integration.

        Args:
            integration_id: The integration ID.

        Returns:
            Integration details.
        """
        response = await self._client._get(f"/api/v1/integrations/{integration_id}")
        return response.json()
