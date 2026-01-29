"""
Type definitions for Modulo API responses.
"""

from .common import (
    APIResponse,
    PaginatedContent,
    RequestInfo,
)
from .integrations import (
    AuthScheme,
    CredentialProperty,
    Credentials,
    Integration,
    IntegrationListData,
    IntegrationListResponse,
    IntegrationRetrieveResponse,
)
from .kits import (
    Kit,
    KitAuthScheme,
    KitListData,
    KitListResponse,
    KitRetrieveResponse,
)
from .actions import (
    Action,
    ActionConfig,
    ActionExecuteData,
    ActionExecuteResponse,
    ActionListData,
    ActionListResponse,
    ActionRetrieveResponse,
    InputParameterProperty,
    InputParameters,
)

__all__ = [
    # Common
    "APIResponse",
    "PaginatedContent",
    "RequestInfo",
    # Integrations
    "AuthScheme",
    "CredentialProperty",
    "Credentials",
    "Integration",
    "IntegrationListData",
    "IntegrationListResponse",
    "IntegrationRetrieveResponse",
    # Kits
    "Kit",
    "KitAuthScheme",
    "KitListData",
    "KitListResponse",
    "KitRetrieveResponse",
    # Actions
    "Action",
    "ActionConfig",
    "ActionExecuteData",
    "ActionExecuteResponse",
    "ActionListData",
    "ActionListResponse",
    "ActionRetrieveResponse",
    "InputParameterProperty",
    "InputParameters",
]
