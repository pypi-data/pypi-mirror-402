"""Core types and utilities for the integrations SDK."""

from nospoon_integrations.core.errors import (
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
    ProviderEndpoints,
    TokenData,
    TokenRefreshResult,
    TokenStorage,
)

__all__ = [
    "ConnectionStatus",
    "IntegrationError",
    "OAuthCallbackParams",
    "OAuthError",
    "ProviderAPIError",
    "ProviderConfig",
    "ProviderEndpoints",
    "TokenData",
    "TokenExpiredError",
    "TokenNotFoundError",
    "TokenRefreshError",
    "TokenRefreshResult",
    "TokenStorage",
]
