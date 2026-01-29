"""
Type definitions for Actions.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class InputParameterProperty(TypedDict, total=False):
    """Input parameter property definition."""
    type: str
    description: Optional[str]
    location: Optional[str]


class InputParameters(TypedDict, total=False):
    """Input parameters schema."""
    properties: dict[str, InputParameterProperty]
    required: list[str]


class ActionConfig(TypedDict, total=False):
    """Action config."""
    method: str
    url: str
    retry_config: dict[str, Any]


class Action(TypedDict, total=False):
    """Action object."""
    id: str
    slug: str
    integration_id: str
    name: str
    display_name: str
    description: str
    input_parameters: InputParameters
    output_parameters: Optional[dict[str, Any]]
    scopes: list[str]
    status: str
    version: int
    config: ActionConfig
    documentation_url: Optional[str]
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class ActionListData(TypedDict):
    """Data field for list actions response."""
    content: list[Action]
    total: int
    page: int
    size: int


class ActionListResponse(TypedDict, total=False):
    """Response from list actions."""
    status: str
    message: str
    data: ActionListData
    traceback: Optional[str]
    code: int


class ActionRetrieveResponse(TypedDict, total=False):
    """Response from retrieve action."""
    status: str
    message: str
    data: Action
    traceback: Optional[str]
    code: int


class ActionExecuteData(TypedDict, total=False):
    """Data field for execute action response."""
    execution_id: str
    integration_kit_id: str
    action_id: str
    success: bool
    data: Any
    error: Optional[str]
    duration_ms: int
    timestamp: str


class ActionExecuteResponse(TypedDict, total=False):
    """Response from execute action."""
    status: str
    message: str
    data: ActionExecuteData
    traceback: Optional[str]
    code: int
