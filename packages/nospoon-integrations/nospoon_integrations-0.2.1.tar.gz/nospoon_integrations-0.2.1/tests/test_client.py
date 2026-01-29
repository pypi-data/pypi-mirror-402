"""Tests for IntegrationClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nospoon_integrations.client import IntegrationClient
from nospoon_integrations.core.types import ProviderConfig, TokenData
from nospoon_integrations.storage.memory import MemoryTokenStorage


class TestIntegrationClient:
    """Tests for the unified IntegrationClient."""

    @pytest.fixture
    def storage(self):
        """Create a fresh storage instance."""
        return MemoryTokenStorage()

    def test_creates_client_with_no_providers(self, storage):
        """Should create client with no providers."""
        client = IntegrationClient(storage=storage)
        assert client.google is None
        assert client.hubspot is None
        assert client.facebook is None
        assert client.linkedin is None

    def test_creates_client_with_google_provider(self, storage):
        """Should create client with Google provider."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(
                client_id="google-id",
                client_secret="google-secret",
            ),
        )

        assert client.google is not None
        assert client.hubspot is None

    def test_creates_client_with_multiple_providers(self, storage):
        """Should create client with multiple providers."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(
                client_id="google-id",
                client_secret="google-secret",
            ),
            hubspot=ProviderConfig(
                client_id="hubspot-id",
                client_secret="hubspot-secret",
            ),
        )

        assert client.google is not None
        assert client.hubspot is not None

    def test_creates_client_with_all_providers(self, storage):
        """Should create client with all providers."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(client_id="g-id", client_secret="g-secret"),
            hubspot=ProviderConfig(client_id="h-id", client_secret="h-secret"),
            facebook=ProviderConfig(client_id="f-id", client_secret="f-secret"),
            linkedin=ProviderConfig(client_id="l-id", client_secret="l-secret"),
        )

        assert client.google is not None
        assert client.hubspot is not None
        assert client.facebook is not None
        assert client.linkedin is not None

    def test_get_providers_returns_empty_list(self, storage):
        """Should return empty list when no providers configured."""
        client = IntegrationClient(storage=storage)
        assert client.get_providers() == []

    def test_get_providers_returns_configured_providers(self, storage):
        """Should return list of configured providers."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(client_id="id", client_secret="secret"),
            hubspot=ProviderConfig(client_id="id", client_secret="secret"),
        )

        providers = client.get_providers()
        assert "google" in providers
        assert "hubspot" in providers
        assert len(providers) == 2

    @pytest.mark.asyncio
    async def test_get_all_connection_statuses(self, storage):
        """Should return statuses for all configured providers."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(client_id="id", client_secret="secret"),
            hubspot=ProviderConfig(client_id="id", client_secret="secret"),
        )

        # Store a token for Google only
        await storage.save_token(
            "user-123",
            "google",
            TokenData(access_token="token", refresh_token="refresh"),
        )

        statuses = await client.get_all_connection_statuses("user-123")

        assert statuses["google"].connected is True
        assert statuses["google"].has_refresh_token is True
        assert statuses["hubspot"].connected is False
        assert statuses["hubspot"].has_refresh_token is False

    @pytest.mark.asyncio
    async def test_get_all_connection_statuses_empty(self, storage):
        """Should return empty dict when no providers configured."""
        client = IntegrationClient(storage=storage)
        statuses = await client.get_all_connection_statuses("user-123")
        assert statuses == {}

    @pytest.mark.asyncio
    async def test_disconnect_all(self, storage):
        """Should disconnect all configured providers."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(client_id="id", client_secret="secret"),
            hubspot=ProviderConfig(client_id="id", client_secret="secret"),
        )

        # Store tokens for both
        await storage.save_token("user-123", "google", TokenData(access_token="google-token"))
        await storage.save_token("user-123", "hubspot", TokenData(access_token="hubspot-token"))

        # Mock revoke calls for Google (HubSpot doesn't have revoke)
        mock_response = MagicMock()
        mock_response.is_success = True

        with patch.object(client.google._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.disconnect_all("user-123")

        # Verify tokens are deleted
        assert await storage.get_token("user-123", "google") is None
        assert await storage.get_token("user-123", "hubspot") is None

    @pytest.mark.asyncio
    async def test_disconnect_all_no_error_when_not_connected(self, storage):
        """Should not fail when no providers connected."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(client_id="id", client_secret="secret"),
        )

        # Should not raise
        await client.disconnect_all("user-123")

    def test_provider_access(self, storage):
        """Should allow direct provider method calls."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(
                client_id="google-id",
                client_secret="google-secret",
            ),
        )

        # Can call provider methods directly
        auth_url = client.google.get_auth_url("https://example.com/callback")
        assert "accounts.google.com" in auth_url

    @pytest.mark.asyncio
    async def test_storage_shared_across_providers(self, storage):
        """Should share storage across providers."""
        client = IntegrationClient(
            storage=storage,
            google=ProviderConfig(client_id="id", client_secret="secret"),
            hubspot=ProviderConfig(client_id="id", client_secret="secret"),
        )

        # Store via Google
        await client.google.store_external_tokens(
            "user-123",
            TokenData(access_token="google-token"),
        )

        # HubSpot shouldn't see it (different provider key)
        hubspot_status = await client.hubspot.get_connection_status("user-123")
        assert hubspot_status.connected is False

        # But Google should
        google_status = await client.google.get_connection_status("user-123")
        assert google_status.connected is True
