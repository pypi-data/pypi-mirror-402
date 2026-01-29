"""NoSpoon Integrations SDK - Cross-platform OAuth integrations."""

from nospoon_integrations.client import IntegrationClient
from nospoon_integrations.core.errors import (
    InsufficientScopeError,
    IntegrationError,
    OAuthError,
    ProviderAPIError,
    TokenExpiredError,
    TokenNotFoundError,
    TokenRefreshError,
)
from nospoon_integrations.core.types import (
    ConnectionStatus,
    OAuthCallbackParams,
    ProviderConfig,
    TokenData,
    TokenRefreshResult,
    TokenStorage,
)
from nospoon_integrations.utils.state_token import (
    StateTokenOptions,
    StateTokenPayload,
    StateTokenVerifyResult,
    create_state_token,
    extract_user_id_from_state,
    verify_state_token,
)

__version__ = "0.2.1"

__all__ = [
    "ConnectionStatus",
    "InsufficientScopeError",
    "IntegrationClient",
    "IntegrationError",
    "OAuthCallbackParams",
    "OAuthError",
    "ProviderAPIError",
    "ProviderConfig",
    "StateTokenOptions",
    "StateTokenPayload",
    "StateTokenVerifyResult",
    "TokenData",
    "TokenExpiredError",
    "TokenNotFoundError",
    "TokenRefreshError",
    "TokenRefreshResult",
    "TokenStorage",
    "__version__",
    "create_state_token",
    "extract_user_id_from_state",
    "verify_state_token",
]
