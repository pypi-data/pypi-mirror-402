"""Tests for HubSpotProvider."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nospoon_integrations.core.errors import TokenNotFoundError
from nospoon_integrations.core.types import ProviderConfig, TokenData
from nospoon_integrations.providers.hubspot import HubSpotContact, HubSpotProvider
from nospoon_integrations.storage.memory import MemoryTokenStorage


class TestHubSpotProvider:
    """Tests for the HubSpot OAuth provider."""

    @pytest.fixture
    def storage(self):
        """Create a fresh storage instance."""
        return MemoryTokenStorage()

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ProviderConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
            scopes=["crm.objects.contacts.read", "crm.objects.contacts.write"],
        )

    @pytest.fixture
    def provider(self, config, storage):
        """Create provider instance."""
        return HubSpotProvider(config, storage)

    def test_get_auth_url_generates_correct_url(self, provider):
        """Should generate correct OAuth URL."""
        redirect_uri = "https://example.com/callback"
        url = provider.get_auth_url(redirect_uri)

        assert "app.hubspot.com/oauth/authorize" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=" in url
        assert "crm.objects.contacts.read" in url

    def test_get_auth_url_includes_state_if_provided(self, provider):
        """Should include state parameter if provided."""
        redirect_uri = "https://example.com/callback"
        state = "random-state-123"
        url = provider.get_auth_url(redirect_uri, state)

        assert f"state={state}" in url

    @pytest.mark.asyncio
    async def test_exchange_code_returns_tokens(self, provider):
        """Should exchange code for tokens."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await provider.exchange_code("auth-code-123", "https://example.com/callback")

            assert result.access_token == "new-access-token"
            assert result.refresh_token == "new-refresh-token"

    @pytest.mark.asyncio
    async def test_refresh_token_returns_new_refresh(self, provider):
        """Should return new refresh token in result."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await provider.refresh_token("old-refresh")
            assert result.refresh_token == "new-refresh"

    @pytest.mark.asyncio
    async def test_get_connection_status(self, provider, storage):
        """Should return connection status."""
        await storage.save_token(
            "user-123",
            "hubspot",
            TokenData(
                access_token="token",
                refresh_token="refresh-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        status = await provider.get_connection_status("user-123")
        assert status.connected is True
        assert status.has_refresh_token is True

    @pytest.mark.asyncio
    async def test_disconnect_deletes_token(self, provider, storage):
        """Should delete stored token."""
        await storage.save_token(
            "user-123",
            "hubspot",
            TokenData(access_token="token", refresh_token="refresh"),
        )

        await provider.disconnect("user-123")

        token = await storage.get_token("user-123", "hubspot")
        assert token is None

    @pytest.mark.asyncio
    async def test_create_contact_new(self, provider, storage):
        """Should create new contact when not found."""
        await storage.save_token(
            "user-123",
            "hubspot",
            TokenData(
                access_token="valid-token",
                refresh_token="refresh-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        # Mock responses in order
        mock_responses = [
            # search - no existing contact
            MagicMock(is_success=True, json=lambda: {"results": []}),
            # create contact
            MagicMock(
                is_success=True,
                json=lambda: {
                    "id": "contact-123",
                    "properties": {"email": "test@example.com"},
                    "createdAt": "2025-01-01T00:00:00Z",
                    "updatedAt": "2025-01-01T00:00:00Z",
                },
            ),
        ]
        response_iter = iter(mock_responses)

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = lambda *args, **kwargs: next(response_iter)

            result, updated = await provider.create_contact(
                "user-123",
                HubSpotContact(
                    contact_person="John Doe",
                    contact_email="john@example.com",
                    company_name="Acme Inc",
                ),
            )

            assert result.id == "contact-123"
            assert updated is False

    @pytest.mark.asyncio
    async def test_create_contact_update_existing(self, provider, storage):
        """Should update existing contact when found."""
        await storage.save_token(
            "user-123",
            "hubspot",
            TokenData(
                access_token="valid-token",
                refresh_token="refresh-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        # Mock responses
        mock_search = MagicMock(
            is_success=True,
            json=lambda: {"results": [{"id": "existing-contact-123"}]},
        )
        mock_update = MagicMock(
            is_success=True,
            json=lambda: {
                "id": "existing-contact-123",
                "properties": {},
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-01T00:00:00Z",
            },
        )

        with (
            patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(provider._client, "patch", new_callable=AsyncMock) as mock_patch,
        ):
            mock_post.return_value = mock_search
            mock_patch.return_value = mock_update

            result, updated = await provider.create_contact(
                "user-123",
                HubSpotContact(contact_email="test@example.com"),
            )

            assert result.id == "existing-contact-123"
            assert updated is True

    @pytest.mark.asyncio
    async def test_create_contact_maps_fields_correctly(self, provider, storage):
        """Should map contact fields correctly."""
        await storage.save_token(
            "user-123",
            "hubspot",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        captured_body = None

        async def capture_post(*args, **kwargs):
            nonlocal captured_body
            if "contacts/search" in str(args):
                return MagicMock(is_success=True, json=lambda: {"results": []})
            else:
                captured_body = kwargs.get("json", {})
                return MagicMock(
                    is_success=True,
                    json=lambda: {
                        "id": "new",
                        "properties": {},
                        "createdAt": "2025-01-01T00:00:00Z",
                        "updatedAt": "2025-01-01T00:00:00Z",
                    },
                )

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = capture_post

            await provider.create_contact(
                "user-123",
                HubSpotContact(
                    contact_person="Jane Smith",
                    contact_email="jane@example.com",
                    company_name="Tech Corp",
                    job_title="CTO",
                    mobile="+1234567890",
                    office_phone="+0987654321",
                    company_website="https://techcorp.com",
                    office_location="123 Main St",
                    industry="Technology",
                ),
            )

            # Verify the mapped properties
            props = captured_body["properties"]
            assert props["firstname"] == "Jane"
            assert props["lastname"] == "Smith"
            assert props["email"] == "jane@example.com"
            assert props["company"] == "Tech Corp"
            assert props["jobtitle"] == "CTO"
            assert props["mobilephone"] == "+1234567890"
            assert props["phone"] == "+0987654321"
            assert props["website"] == "https://techcorp.com"
            assert props["address"] == "123 Main St"
            assert props["industry"] == "Technology"

    @pytest.mark.asyncio
    async def test_create_contact_throws_when_not_connected(self, provider):
        """Should throw TokenNotFoundError when not connected."""
        with pytest.raises(TokenNotFoundError):
            await provider.create_contact(
                "user-123",
                HubSpotContact(contact_email="test@example.com"),
            )

    @pytest.mark.asyncio
    async def test_batch_create_contacts_success(self, provider, storage):
        """Should batch create contacts successfully."""
        await storage.save_token(
            "user-123",
            "hubspot",
            TokenData(
                access_token="valid-token",
                refresh_token="refresh-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        # Mock batch create response
        mock_response = MagicMock(
            is_success=True,
            json=lambda: {
                "results": [
                    {
                        "id": "1",
                        "properties": {},
                        "createdAt": "2025-01-01T00:00:00Z",
                        "updatedAt": "2025-01-01T00:00:00Z",
                    },
                    {
                        "id": "2",
                        "properties": {},
                        "createdAt": "2025-01-01T00:00:00Z",
                        "updatedAt": "2025-01-01T00:00:00Z",
                    },
                ]
            },
        )

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            results, _errors = await provider.batch_create_contacts(
                "user-123",
                [
                    HubSpotContact(contact_email="one@example.com"),
                    HubSpotContact(contact_email="two@example.com"),
                ],
            )

            assert len(results) == 2
