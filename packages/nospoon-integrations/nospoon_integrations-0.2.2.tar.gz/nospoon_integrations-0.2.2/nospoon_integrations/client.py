"""Main IntegrationClient class."""

from typing import Optional

from nospoon_integrations.core.types import (
    ConnectionStatus,
    ProviderConfig,
    TokenStorage,
)
from nospoon_integrations.providers.facebook import FacebookProvider
from nospoon_integrations.providers.google import GoogleProvider
from nospoon_integrations.providers.hubspot import HubSpotProvider
from nospoon_integrations.providers.linkedin import LinkedInProvider


class IntegrationClient:
    """
    Main client for managing OAuth integrations.

    Example:
        ```python
        from nospoon_integrations import IntegrationClient, ProviderConfig
        from nospoon_integrations.storage import SupabaseTokenStorage

        storage = SupabaseTokenStorage(
            supabase_url=os.environ["SUPABASE_URL"],
            supabase_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )

        integrations = IntegrationClient(
            storage=storage,
            google=ProviderConfig(
                client_id=os.environ["GOOGLE_CLIENT_ID"],
                client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
                scopes=["https://www.googleapis.com/auth/gmail.compose"],
            ),
        )

        # Get auth URL
        url = integrations.google.get_auth_url("https://myapp.com/callback")

        # Handle callback
        await integrations.google.handle_callback(user_id, OAuthCallbackParams(code=code, redirect_uri=redirect_uri))

        # Use provider APIs
        await integrations.google.create_draft_email(user_id, DraftEmailParams(to=to, subject=subject, body=body))
        ```
    """

    def __init__(
        self,
        storage: TokenStorage,
        google: Optional[ProviderConfig] = None,
        hubspot: Optional[ProviderConfig] = None,
        facebook: Optional[ProviderConfig] = None,
        linkedin: Optional[ProviderConfig] = None,
    ) -> None:
        self._storage = storage

        self.google: Optional[GoogleProvider] = None
        self.hubspot: Optional[HubSpotProvider] = None
        self.facebook: Optional[FacebookProvider] = None
        self.linkedin: Optional[LinkedInProvider] = None

        if google:
            self.google = GoogleProvider(google, storage)
        if hubspot:
            self.hubspot = HubSpotProvider(hubspot, storage)
        if facebook:
            self.facebook = FacebookProvider(facebook, storage)
        if linkedin:
            self.linkedin = LinkedInProvider(linkedin, storage)

    def get_providers(self) -> list[str]:
        """
        Get all configured providers.

        Returns:
            Array of configured provider names
        """
        providers: list[str] = []
        if self.google:
            providers.append("google")
        if self.hubspot:
            providers.append("hubspot")
        if self.facebook:
            providers.append("facebook")
        if self.linkedin:
            providers.append("linkedin")
        return providers

    async def get_all_connection_statuses(self, user_id: str) -> dict[str, ConnectionStatus]:
        """
        Get connection status for all configured providers.

        Args:
            user_id: User ID to check

        Returns:
            Connection status for each provider
        """
        statuses: dict[str, ConnectionStatus] = {}

        if self.google:
            statuses["google"] = await self.google.get_connection_status(user_id)
        if self.hubspot:
            statuses["hubspot"] = await self.hubspot.get_connection_status(user_id)
        if self.facebook:
            statuses["facebook"] = await self.facebook.get_connection_status(user_id)
        if self.linkedin:
            statuses["linkedin"] = await self.linkedin.get_connection_status(user_id)

        return statuses

    async def disconnect_all(self, user_id: str) -> None:
        """
        Disconnect all providers for a user.
        Useful for GDPR deletion requests.

        Args:
            user_id: User ID to disconnect
        """
        if self.google:
            await self.google.disconnect(user_id)
        if self.hubspot:
            await self.hubspot.disconnect(user_id)
        if self.facebook:
            await self.facebook.disconnect(user_id)
        if self.linkedin:
            await self.linkedin.disconnect(user_id)
