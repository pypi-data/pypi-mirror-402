"""
Modulo Client - Python SDK for Modulo API

Two client types are available:
- ModuloClient: Uses API key authentication (api_key + project_id)
- ModuloS2SClient: Uses RSA signature authentication (service_id + private_key)

Example - API Key Authentication:
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

Example - S2S Authentication (for LiveKit agent workers):
    ```python
    from modulo import ModuloS2SClient

    client = ModuloS2SClient(
        service_id="my-livekit-service",
        private_key_path="/path/to/private.key",
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

Environment Variables:
    MODULO_API_KEY: API key (for ModuloClient)
    MODULO_SERVICE_ID: Service identifier (for ModuloS2SClient)
    MODULO_PRIVATE_KEY: RSA private key content (for ModuloS2SClient)
    MODULO_BASE_URL: Base URL override
"""

from . import _models as models
from ._client import (
    AsyncClient,
    AsyncModuloClient,
    AsyncModuloS2SClient,
    Client,
    ModuloClient,
    ModuloS2SClient,
)
from ._constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, ENVIRONMENTS
from ._exceptions import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    ApiKeyNotProvidedError,
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    ConflictError,
    InternalServerError,
    ModuloError,
    NotFoundError,
    PermissionDeniedError,
    PrivateKeyError,
    PrivateKeyNotProvidedError,
    ProjectIdNotProvidedError,
    RateLimitError,
    ServiceIdNotProvidedError,
    UnprocessableEntityError,
)
from ._types import NOT_GIVEN, NotGiven, RequestOptions, Timeout
from ._version import __title__, __version__

__all__ = [
    # Main clients - API Key auth
    "ModuloClient",
    "AsyncModuloClient",
    # S2S clients - RSA signature auth
    "ModuloS2SClient",
    "AsyncModuloS2SClient",
    # Aliases
    "Client",
    "AsyncClient",
    # Models module
    "models",
    # Type helpers
    "NOT_GIVEN",
    "NotGiven",
    "RequestOptions",
    "Timeout",
    # Constants
    "ENVIRONMENTS",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    # Version
    "__version__",
    "__title__",
    # Exceptions
    "ModuloError",
    "ConfigurationError",
    "ApiKeyNotProvidedError",
    "ServiceIdNotProvidedError",
    "PrivateKeyNotProvidedError",
    "ProjectIdNotProvidedError",
    "PrivateKeyError",
    "APIError",
    "APIStatusError",
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "APIConnectionError",
    "APITimeoutError",
    "APIResponseValidationError",
]
