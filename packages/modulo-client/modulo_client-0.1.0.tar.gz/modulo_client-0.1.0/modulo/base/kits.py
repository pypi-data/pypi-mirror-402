"""
Kits resource for the Modulo client.
"""

from __future__ import annotations

import typing as t

from .._types import NOT_GIVEN, NotGiven

if t.TYPE_CHECKING:
    from .._base_client import AsyncAPIClient, AsyncS2SAPIClient, SyncAPIClient, SyncS2SAPIClient
    from .._models.kits import (
        KitListResponse,
        KitRetrieveResponse,
    )


class KitsResource:
    """Sync resource for managing kits."""

    _client: t.Union["SyncAPIClient", "SyncS2SAPIClient"]

    def __init__(self, client: t.Union["SyncAPIClient", "SyncS2SAPIClient"]) -> None:
        self._client = client

    def retrieve(
        self,
        kit_id: str,
    ) -> "KitRetrieveResponse":
        """
        Retrieve detailed information about a kit.

        Args:
            kit_id: The ID of the kit.

        Returns:
            Kit details.
        """
        response = self._client._get(f"/api/v1/integration-kits/{kit_id}")
        return response.json()

    def list(
        self,
        *,
        page: t.Union[int, NotGiven] = NOT_GIVEN,
        size: t.Union[int, NotGiven] = NOT_GIVEN,
    ) -> "KitListResponse":
        """
        List kits.

        Args:
            page: Page number for pagination.
            size: Number of items per page.

        Returns:
            Paginated list of kits.
        """
        params: dict[str, t.Any] = {}
        if not isinstance(page, NotGiven):
            params["page"] = page
        if not isinstance(size, NotGiven):
            params["size"] = size

        response = self._client._get("/api/v1/integration-kits", params=params if params else None)
        return response.json()

    def delete(
        self,
        kit_id: str,
    ) -> dict[str, t.Any]:
        """
        Delete a kit.

        Args:
            kit_id: The ID of the kit to delete.

        Returns:
            Deletion confirmation.
        """
        response = self._client._delete(f"/api/v1/integration-kits/{kit_id}")
        return response.json()


class AsyncKitsResource:
    """Async resource for managing kits."""

    _client: t.Union["AsyncAPIClient", "AsyncS2SAPIClient"]

    def __init__(self, client: t.Union["AsyncAPIClient", "AsyncS2SAPIClient"]) -> None:
        self._client = client

    async def retrieve(
        self,
        kit_id: str,
    ) -> "KitRetrieveResponse":
        """
        Retrieve detailed information about a kit.

        Args:
            kit_id: The ID of the kit.

        Returns:
            Kit details.
        """
        response = await self._client._get(f"/api/v1/integration-kits/{kit_id}")
        return response.json()

    async def list(
        self,
        *,
        page: t.Union[int, NotGiven] = NOT_GIVEN,
        size: t.Union[int, NotGiven] = NOT_GIVEN,
    ) -> "KitListResponse":
        """
        List kits.

        Args:
            page: Page number for pagination.
            size: Number of items per page.

        Returns:
            Paginated list of kits.
        """
        params: dict[str, t.Any] = {}
        if not isinstance(page, NotGiven):
            params["page"] = page
        if not isinstance(size, NotGiven):
            params["size"] = size

        response = await self._client._get("/api/v1/integration-kits", params=params if params else None)
        return response.json()

    async def delete(
        self,
        kit_id: str,
    ) -> dict[str, t.Any]:
        """
        Delete a kit.

        Args:
            kit_id: The ID of the kit to delete.

        Returns:
            Deletion confirmation.
        """
        response = await self._client._delete(f"/api/v1/integration-kits/{kit_id}")
        return response.json()
