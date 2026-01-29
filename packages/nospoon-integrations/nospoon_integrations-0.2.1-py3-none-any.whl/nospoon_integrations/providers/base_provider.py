"""Base OAuth provider class."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from urllib.parse import urlencode

import httpx

from nospoon_integrations.core.errors import (
    OAuthError,
    TokenExpiredError,
    TokenNotFoundError,
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
from nospoon_integrations.utils.state_token import (
    create_state_token,
    verify_state_token,
)


@dataclass
class SecureCallbackSuccess:
    """Successful secure callback result."""

    success: bool
    user_id: str
    tokens: TokenData

    def __init__(self, user_id: str, tokens: TokenData):
        self.success = True
        self.user_id = user_id
        self.tokens = tokens


@dataclass
class SecureCallbackFailure:
    """Failed secure callback result."""

    success: bool
    error: str

    def __init__(self, error: str):
        self.success = False
        self.error = error


SecureCallbackResult = Union[SecureCallbackSuccess, SecureCallbackFailure]


class BaseProvider:
    """
    Base class for OAuth providers.

    Provides common functionality for:
    - Generating OAuth authorization URLs
    - Exchanging authorization codes for tokens
    - Refreshing tokens
    - Storing and retrieving tokens
    - Checking connection status

    Subclasses can override protected methods to customize behavior
    for provider-specific requirements.
    """

    def __init__(
        self,
        provider_name: str,
        endpoints: ProviderEndpoints,
        config: ProviderConfig,
        storage: TokenStorage,
        token_refresh_buffer_minutes: int = 5,
    ) -> None:
        self._provider_name = provider_name
        self._endpoints = endpoints
        self._config = config
        self._storage = storage
        self._token_refresh_buffer = timedelta(minutes=token_refresh_buffer_minutes)
        self._client = httpx.AsyncClient()

    async def __aenter__(self) -> "BaseProvider":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._provider_name

    def get_auth_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        additional_params: Optional[dict[str, str]] = None,
    ) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            redirect_uri: URL to redirect to after authorization
            state: Optional state parameter for CSRF protection
            additional_params: Additional query parameters to include

        Returns:
            The authorization URL
        """
        params: dict[str, str] = {
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self._config.scopes or []),
        }
        if state:
            params["state"] = state
        if additional_params:
            params.update(additional_params)

        return f"{self._endpoints.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> TokenData:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Redirect URI used in authorization request

        Returns:
            Token data
        """
        response = await self._client.post(
            self._endpoints.token_url,
            headers=self._get_token_request_headers(),
            content=self._get_token_request_body(code, redirect_uri),
        )

        if not response.is_success:
            raise OAuthError(self._provider_name, f"Token exchange failed: {response.text}")

        return self._parse_token_response(response.json())

    async def handle_callback(self, user_id: str, params: OAuthCallbackParams) -> TokenData:
        """
        Handle OAuth callback - exchange code and store tokens.

        Args:
            user_id: User ID to store tokens for
            params: OAuth callback parameters

        Returns:
            Token data
        """
        tokens = await self.exchange_code(params.code, params.redirect_uri)
        await self._storage.save_tokens(user_id, self._provider_name, tokens)
        return tokens

    async def get_valid_token(self, user_id: str) -> str:
        """
        Get valid access token, refreshing if necessary.

        Args:
            user_id: User ID to get token for

        Returns:
            Valid access token

        Raises:
            TokenNotFoundError: If no tokens exist
            TokenExpiredError: If token is expired and cannot be refreshed
        """
        tokens = await self._storage.get_tokens(user_id, self._provider_name)

        if not tokens:
            raise TokenNotFoundError(self._provider_name)

        if self._is_token_expired(tokens):
            if not tokens.refresh_token:
                raise TokenExpiredError(self._provider_name, reason="No refresh token available")

            refreshed = await self.refresh_token(tokens.refresh_token)
            new_tokens = TokenData(
                access_token=refreshed.access_token,
                refresh_token=refreshed.refresh_token or tokens.refresh_token,
                expires_at=datetime.now() + timedelta(seconds=refreshed.expires_in),
                scope=refreshed.scope or tokens.scope,
            )
            await self._storage.save_tokens(user_id, self._provider_name, new_tokens)
            return new_tokens.access_token

        return tokens.access_token

    async def refresh_token(self, refresh_token: str) -> TokenRefreshResult:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            Refreshed token data
        """
        response = await self._client.post(
            self._endpoints.token_url,
            headers=self._get_token_request_headers(),
            content=self._get_refresh_token_request_body(refresh_token),
        )

        if not response.is_success:
            raise OAuthError(self._provider_name, f"Token refresh failed: {response.text}")

        return self._parse_refresh_token_response(response.json())

    async def get_connection_status(self, user_id: str) -> ConnectionStatus:
        """
        Get connection status for user.

        Args:
            user_id: User ID to check

        Returns:
            Connection status
        """
        tokens = await self._storage.get_tokens(user_id, self._provider_name)

        if not tokens:
            return ConnectionStatus(connected=False, has_refresh_token=False)

        return ConnectionStatus(
            connected=True,
            has_refresh_token=bool(tokens.refresh_token),
            expires_at=tokens.expires_at,
            scopes=tokens.scope.split() if tokens.scope else None,
        )

    async def disconnect(self, user_id: str) -> None:
        """
        Disconnect - remove stored tokens.

        Args:
            user_id: User ID to disconnect
        """
        if self._endpoints.revoke_url:
            try:
                tokens = await self._storage.get_tokens(user_id, self._provider_name)
                if tokens:
                    await self._revoke_token(tokens.access_token)
            except Exception as e:
                print(f"Warning: Failed to revoke {self._provider_name} token: {e}")

        await self._storage.delete_tokens(user_id, self._provider_name)

    async def store_external_tokens(self, user_id: str, tokens: TokenData) -> None:
        """
        Store tokens from external source (e.g., Supabase Auth callback).

        Args:
            user_id: User ID to store tokens for
            tokens: Token data to store
        """
        existing = await self._storage.get_tokens(user_id, self._provider_name)

        if existing and existing.refresh_token and not tokens.refresh_token:
            # Keep existing refresh token, update access token
            await self._storage.save_tokens(
                user_id,
                self._provider_name,
                TokenData(
                    access_token=tokens.access_token,
                    refresh_token=existing.refresh_token,
                    expires_at=tokens.expires_at,
                    scope=tokens.scope,
                ),
            )
        else:
            await self._storage.save_tokens(user_id, self._provider_name, tokens)

    async def has_required_scopes(self, user_id: str, required_scopes: list[str]) -> bool:
        """
        Check if the user has all required scopes.

        Args:
            user_id: User ID to check
            required_scopes: List of required scope strings

        Returns:
            True if all required scopes are granted
        """
        missing_scopes = await self.get_missing_scopes(user_id, required_scopes)
        return len(missing_scopes) == 0

    async def get_missing_scopes(self, user_id: str, required_scopes: list[str]) -> list[str]:
        """
        Get the list of required scopes that are not granted.

        Args:
            user_id: User ID to check
            required_scopes: List of required scope strings

        Returns:
            List of missing scope strings
        """
        tokens = await self._storage.get_tokens(user_id, self._provider_name)

        if not tokens:
            return required_scopes  # All scopes missing if no tokens

        if not tokens.scope:
            return required_scopes  # All scopes missing if no scope stored

        granted_scopes = tokens.scope.split()
        return [scope for scope in required_scopes if scope not in granted_scopes]

    async def get_granted_scopes(self, user_id: str) -> list[str]:
        """
        Get the currently granted scopes for a user.

        Args:
            user_id: User ID to check

        Returns:
            List of granted scope strings, or empty list if none
        """
        tokens = await self._storage.get_tokens(user_id, self._provider_name)

        if not tokens or not tokens.scope:
            return []

        return tokens.scope.split()

    # Secure OAuth Flow Methods

    def generate_secure_auth_url(
        self,
        user_id: str,
        redirect_uri: str,
        secret: str,
        additional_params: Optional[dict[str, str]] = None,
    ) -> str:
        """
        Generate a secure OAuth authorization URL with a signed state token.

        This method creates a CSRF-protected authorization URL by embedding
        a signed state token containing the user ID and timestamp.

        Args:
            user_id: User ID to embed in the state token
            redirect_uri: URL to redirect to after authorization
            secret: Secret key for signing the state token
            additional_params: Additional query parameters to include

        Returns:
            The secure authorization URL

        Example:
            ```python
            url = provider.generate_secure_auth_url(
                user_id,
                "https://myapp.com/callback",
                os.environ["OAUTH_STATE_SECRET"]
            )
            # Redirect user to this URL
            ```
        """
        state = create_state_token(user_id, secret)
        return self.get_auth_url(redirect_uri, state, additional_params)

    async def handle_secure_callback(
        self,
        code: str,
        state: str,
        redirect_uri: str,
        secret: str,
    ) -> SecureCallbackResult:
        """
        Handle OAuth redirect callback with state verification.

        This method verifies the state token signature and expiration,
        then exchanges the authorization code for tokens.

        Args:
            code: Authorization code from the callback
            state: State token from the callback
            redirect_uri: Redirect URI used in the authorization request
            secret: Secret key used for signing the state token

        Returns:
            SecureCallbackResult containing either success with user_id and tokens,
            or failure with error message

        Example:
            ```python
            result = await provider.handle_secure_callback(
                code,
                state,
                "https://myapp.com/callback",
                os.environ["OAUTH_STATE_SECRET"]
            )
            if result.success:
                print(f"User: {result.user_id}")
            else:
                print(f"Error: {result.error}")
            ```
        """
        # Verify state token
        state_result = verify_state_token(state, secret)

        if not state_result.valid or not state_result.user_id:
            return SecureCallbackFailure(state_result.error or "Invalid state token")

        try:
            # Exchange code for tokens
            tokens = await self.exchange_code(code, redirect_uri)

            # Save tokens
            await self._storage.save_tokens(state_result.user_id, self._provider_name, tokens)

            return SecureCallbackSuccess(state_result.user_id, tokens)
        except Exception as e:
            return SecureCallbackFailure(str(e) if str(e) else "Token exchange failed")

    # Protected methods for subclass customization

    def _is_token_expired(self, tokens: TokenData) -> bool:
        """Check if token is expired or will expire soon."""
        if not tokens.expires_at:
            return False
        return datetime.now() + self._token_refresh_buffer >= tokens.expires_at

    def _get_token_request_headers(self) -> dict[str, str]:
        """Get headers for token requests."""
        return {"Content-Type": "application/x-www-form-urlencoded"}

    def _get_token_request_body(self, code: str, redirect_uri: str) -> str:
        """Get body for token exchange request."""
        return urlencode(
            {
                "grant_type": "authorization_code",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            }
        )

    def _get_refresh_token_request_body(self, refresh_token: str) -> str:
        """Get body for token refresh request."""
        return urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "refresh_token": refresh_token,
            }
        )

    def _parse_token_response(self, data: dict[str, Any]) -> TokenData:
        """Parse token response from provider."""
        expires_in = data.get("expires_in")
        return TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=(datetime.now() + timedelta(seconds=expires_in) if expires_in else None),
            scope=data.get("scope"),
            token_type=data.get("token_type"),
        )

    def _parse_refresh_token_response(self, data: dict[str, Any]) -> TokenRefreshResult:
        """Parse refresh token response from provider."""
        return TokenRefreshResult(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in", 3600),
            scope=data.get("scope"),
        )

    async def _revoke_token(self, token: str) -> None:
        """Revoke token with provider."""
        if not self._endpoints.revoke_url:
            return

        await self._client.post(
            self._endpoints.revoke_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            content=urlencode({"token": token}),
        )
