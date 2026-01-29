"""Core types and interfaces for the NoSpoon Integrations SDK."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable


@dataclass
class TokenData:
    """OAuth token data stored per user."""

    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None


@dataclass
class ProviderConfig:
    """Provider configuration provided by the consuming app."""

    client_id: str
    client_secret: str
    scopes: Optional[list[str]] = None
    redirect_uri: Optional[str] = None


@dataclass
class ProviderEndpoints:
    """OAuth provider endpoints."""

    auth_url: str
    token_url: str
    revoke_url: Optional[str] = None
    user_info_url: Optional[str] = None


@dataclass
class ConnectionStatus:
    """Connection status for a user's provider integration."""

    connected: bool
    has_refresh_token: bool
    expires_at: Optional[datetime] = None
    scopes: Optional[list[str]] = None


@dataclass
class TokenRefreshResult:
    """Result from token refresh operation."""

    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int = 3600
    scope: Optional[str] = None


@dataclass
class OAuthCallbackParams:
    """OAuth callback parameters."""

    code: str
    redirect_uri: str
    state: Optional[str] = None


@dataclass
class RawTokenResponse:
    """Raw token response from OAuth provider."""

    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None


@runtime_checkable
class TokenStorage(Protocol):
    """
    Storage interface for token persistence.
    Implement this protocol to use custom storage backends.
    """

    async def get_tokens(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Get tokens for a user and provider."""
        ...

    async def save_tokens(self, user_id: str, provider: str, tokens: TokenData) -> None:
        """Save tokens for a user and provider."""
        ...

    async def delete_tokens(self, user_id: str, provider: str) -> None:
        """Delete tokens for a user and provider."""
        ...

    async def has_tokens(self, user_id: str, provider: str) -> bool:
        """Check if tokens exist for a user and provider."""
        ...
