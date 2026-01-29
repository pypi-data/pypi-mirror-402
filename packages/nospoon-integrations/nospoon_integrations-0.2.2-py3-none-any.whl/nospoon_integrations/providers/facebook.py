"""Facebook OAuth provider with Graph API support."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlencode

from nospoon_integrations.core.errors import ProviderAPIError
from nospoon_integrations.core.types import (
    ProviderConfig,
    ProviderEndpoints,
    TokenData,
    TokenRefreshResult,
    TokenStorage,
)
from nospoon_integrations.providers.base_provider import BaseProvider

FACEBOOK_ENDPOINTS = ProviderEndpoints(
    auth_url="https://www.facebook.com/v18.0/dialog/oauth",
    token_url="https://graph.facebook.com/v18.0/oauth/access_token",
    user_info_url="https://graph.facebook.com/me",
)

GRAPH_API_URL = "https://graph.facebook.com/v18.0"


@dataclass
class FacebookUserInfo:
    """Facebook user info."""

    id: str
    name: str
    email: Optional[str] = None
    picture_url: Optional[str] = None


@dataclass
class FacebookPage:
    """Facebook Page info."""

    id: str
    name: str
    access_token: str


class FacebookProvider(BaseProvider):
    """
    Facebook OAuth provider with Graph API support.

    Note: Facebook uses long-lived tokens instead of refresh tokens.
    Short-lived tokens are automatically exchanged for long-lived tokens.
    """

    def __init__(self, config: ProviderConfig, storage: TokenStorage) -> None:
        default_scopes = config.scopes or ["email", "public_profile"]
        config_with_scopes = ProviderConfig(
            client_id=config.client_id,
            client_secret=config.client_secret,
            scopes=default_scopes,
            redirect_uri=config.redirect_uri,
        )
        super().__init__("facebook", FACEBOOK_ENDPOINTS, config_with_scopes, storage)

    async def exchange_code(self, code: str, redirect_uri: str) -> TokenData:
        """Override exchangeCode to also exchange for long-lived token."""
        params = urlencode(
            {
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            }
        )

        response = await self._client.get(f"{self._endpoints.token_url}?{params}")

        if not response.is_success:
            raise ProviderAPIError(
                "facebook", response.status_code, "Token exchange failed", response.text
            )

        data: dict[str, Any] = response.json()

        # Exchange short-lived token for long-lived token
        return await self._exchange_for_long_lived_token(data["access_token"])

    async def refresh_token(self, existing_token: str) -> TokenRefreshResult:
        """Facebook doesn't use refresh tokens - exchange for long-lived token instead."""
        params = urlencode(
            {
                "grant_type": "fb_exchange_token",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "fb_exchange_token": existing_token,
            }
        )

        response = await self._client.get(f"{self._endpoints.token_url}?{params}")

        if not response.is_success:
            raise ProviderAPIError("facebook", response.status_code, "Failed to refresh token")

        data: dict[str, Any] = response.json()
        return TokenRefreshResult(
            access_token=data["access_token"],
            expires_in=data.get("expires_in", 5184000),  # 60 days default
        )

    async def _exchange_for_long_lived_token(self, short_lived_token: str) -> TokenData:
        """Exchange short-lived token for long-lived token (60 days)."""
        params = urlencode(
            {
                "grant_type": "fb_exchange_token",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "fb_exchange_token": short_lived_token,
            }
        )

        response = await self._client.get(f"{self._endpoints.token_url}?{params}")

        if not response.is_success:
            # Fall back to short-lived token if exchange fails
            return TokenData(
                access_token=short_lived_token,
                expires_at=datetime.now() + timedelta(hours=1),
            )

        data: dict[str, Any] = response.json()
        expires_in = data.get("expires_in", 5184000)
        return TokenData(
            access_token=data["access_token"],
            # Store long-lived token as "refresh token" for future exchanges
            refresh_token=data["access_token"],
            expires_at=datetime.now() + timedelta(seconds=expires_in),
        )

    # Facebook-specific API methods

    async def get_user_info(self, user_id: str) -> FacebookUserInfo:
        """
        Get user info from Facebook.

        Args:
            user_id: User ID

        Returns:
            Facebook user info
        """
        access_token = await self.get_valid_token(user_id)

        response = await self._client.get(
            f"{GRAPH_API_URL}/me?fields=id,name,email,picture&access_token={access_token}"
        )

        if not response.is_success:
            raise ProviderAPIError(
                "facebook",
                response.status_code,
                "Failed to get user info",
                response.text,
            )

        data: dict[str, Any] = response.json()
        return FacebookUserInfo(
            id=data["id"],
            name=data["name"],
            email=data.get("email"),
            picture_url=data.get("picture", {}).get("data", {}).get("url"),
        )

    async def get_pages(self, user_id: str) -> list[FacebookPage]:
        """
        Get user's Facebook Pages (requires pages_show_list permission).

        Args:
            user_id: User ID

        Returns:
            Array of Facebook pages
        """
        access_token = await self.get_valid_token(user_id)

        response = await self._client.get(
            f"{GRAPH_API_URL}/me/accounts?access_token={access_token}"
        )

        if not response.is_success:
            raise ProviderAPIError(
                "facebook", response.status_code, "Failed to get pages", response.text
            )

        data: dict[str, Any] = response.json()
        return [
            FacebookPage(
                id=page["id"],
                name=page["name"],
                access_token=page["access_token"],
            )
            for page in data.get("data", [])
        ]

    async def post_to_page(self, user_id: str, page_id: str, message: str) -> dict[str, str]:
        """
        Post to a Facebook Page.

        Args:
            user_id: User ID
            page_id: Page ID
            message: Message to post

        Returns:
            Post result with ID
        """
        # First get page access token
        pages = await self.get_pages(user_id)
        page = next((p for p in pages if p.id == page_id), None)

        if not page:
            raise ProviderAPIError("facebook", 404, f"Page {page_id} not found or not accessible")

        response = await self._client.post(
            f"{GRAPH_API_URL}/{page_id}/feed",
            headers={"Content-Type": "application/json"},
            json={"message": message, "access_token": page.access_token},
        )

        if not response.is_success:
            raise ProviderAPIError(
                "facebook",
                response.status_code,
                "Failed to post to page",
                response.text,
            )

        result: dict[str, str] = response.json()
        return result
