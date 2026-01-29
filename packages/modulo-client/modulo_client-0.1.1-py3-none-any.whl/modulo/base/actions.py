"""
Actions resource for the Modulo client.
"""

from __future__ import annotations

import typing as t

from .._types import NOT_GIVEN, NotGiven

if t.TYPE_CHECKING:
    from .._base_client import AsyncAPIClient, AsyncS2SAPIClient, SyncAPIClient, SyncS2SAPIClient
    from .._models.actions import (
        ActionExecuteResponse,
        ActionListResponse,
        ActionRetrieveResponse,
    )


class ActionsResource:
    """Sync resource for managing actions."""

    _client: t.Union["SyncAPIClient", "SyncS2SAPIClient"]

    def __init__(self, client: t.Union["SyncAPIClient", "SyncS2SAPIClient"]) -> None:
        self._client = client

    def retrieve(
        self,
        kit_id: str,
        action_id: str,
    ) -> "ActionRetrieveResponse":
        """
        Retrieve detailed information about a specific action.

        Args:
            kit_id: The ID of the integration kit.
            action_id: The ID of the action.

        Returns:
            Action details including input/output parameters and metadata.
        """
        response = self._client._get(
            f"/v1/integration-kits/{kit_id}/actions/{action_id}"
        )
        return response.json()

    def list(
        self,
        kit_id: str,
        *,
        page: t.Union[int, NotGiven] = NOT_GIVEN,
        size: t.Union[int, NotGiven] = NOT_GIVEN,
    ) -> "ActionListResponse":
        """
        List available actions for an integration kit.

        Args:
            kit_id: The ID of the integration kit.
            page: Page number for pagination.
            size: Number of items per page.

        Returns:
            Paginated list of actions.
        """
        params: dict[str, t.Any] = {}
        if not isinstance(page, NotGiven):
            params["page"] = page
        if not isinstance(size, NotGiven):
            params["size"] = size

        response = self._client._get(
            f"/v1/integration-kits/{kit_id}/actions",
            params=params if params else None,
        )
        return response.json()

    def execute(
        self,
        kit_id: str,
        action_id: str,
        *,
        arguments: t.Union[dict[str, t.Any], NotGiven] = NOT_GIVEN,
    ) -> "ActionExecuteResponse":
        """
        Execute an action with the provided parameters.

        Args:
            kit_id: The ID of the integration kit.
            action_id: The ID of the action to execute.
            arguments: Key-value pairs of arguments for the action.

        Returns:
            Action execution response with data or error.
        """
        body: dict[str, t.Any] = {}
        if not isinstance(arguments, NotGiven):
            body["arguments"] = arguments

        response = self._client._post(
            f"/v1/integration-kits/{kit_id}/actions/{action_id}/execute",
            json=body if body else None,
        )
        return response.json()


class AsyncActionsResource:
    """Async resource for managing actions."""

    _client: t.Union["AsyncAPIClient", "AsyncS2SAPIClient"]

    def __init__(self, client: t.Union["AsyncAPIClient", "AsyncS2SAPIClient"]) -> None:
        self._client = client

    async def retrieve(
        self,
        kit_id: str,
        action_id: str,
    ) -> "ActionRetrieveResponse":
        """
        Retrieve detailed information about a specific action.

        Args:
            kit_id: The ID of the integration kit.
            action_id: The ID of the action.

        Returns:
            Action details including input/output parameters and metadata.
        """
        response = await self._client._get(
            f"/v1/integration-kits/{kit_id}/actions/{action_id}"
        )
        return response.json()

    async def list(
        self,
        kit_id: str,
        *,
        page: t.Union[int, NotGiven] = NOT_GIVEN,
        size: t.Union[int, NotGiven] = NOT_GIVEN,
    ) -> "ActionListResponse":
        """
        List available actions for an integration kit.

        Args:
            kit_id: The ID of the integration kit.
            page: Page number for pagination.
            size: Number of items per page.

        Returns:
            Paginated list of actions.
        """
        params: dict[str, t.Any] = {}
        if not isinstance(page, NotGiven):
            params["page"] = page
        if not isinstance(size, NotGiven):
            params["size"] = size

        response = await self._client._get(
            f"/v1/integration-kits/{kit_id}/actions",
            params=params if params else None,
        )
        return response.json()

    async def execute(
        self,
        kit_id: str,
        action_id: str,
        *,
        arguments: t.Union[dict[str, t.Any], NotGiven] = NOT_GIVEN,
    ) -> "ActionExecuteResponse":
        """
        Execute an action with the provided parameters.

        Args:
            kit_id: The ID of the integration kit.
            action_id: The ID of the action to execute.
            arguments: Key-value pairs of arguments for the action.

        Returns:
            Action execution response with data or error.
        """
        body: dict[str, t.Any] = {}
        if not isinstance(arguments, NotGiven):
            body["arguments"] = arguments

        response = await self._client._post(
            f"/v1/integration-kits/{kit_id}/actions/{action_id}/execute",
            json=body if body else None,
        )
        return response.json()
