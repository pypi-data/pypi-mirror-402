"""Tests for MicrosoftProvider."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nospoon_integrations.core.errors import ProviderAPIError, TokenNotFoundError
from nospoon_integrations.core.types import OAuthCallbackParams, ProviderConfig, TokenData
from nospoon_integrations.providers.microsoft import (
    MicrosoftProvider,
    MicrosoftSendEmailParams,
)
from nospoon_integrations.storage.memory import MemoryTokenStorage


class TestMicrosoftProvider:
    """Tests for the Microsoft OAuth provider."""

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
            scopes=["Mail.Send", "User.Read", "offline_access"],
        )

    @pytest.fixture
    def provider(self, config, storage):
        """Create provider instance."""
        return MicrosoftProvider(config, storage)

    def test_get_auth_url_generates_correct_url(self, provider):
        """Should generate correct OAuth URL with common tenant."""
        redirect_uri = "https://example.com/callback"
        url = provider.get_auth_url(redirect_uri)

        assert "login.microsoftonline.com/common/oauth2/v2.0/authorize" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=" in url
        assert "response_type=code" in url
        assert "response_mode=query" in url
        assert "prompt=consent" in url

    def test_get_auth_url_with_custom_tenant(self, config, storage):
        """Should use custom tenant when specified."""
        custom_provider = MicrosoftProvider(config, storage, tenant="my-tenant-id")
        url = custom_provider.get_auth_url("https://example.com/callback")

        assert "login.microsoftonline.com/my-tenant-id/oauth2/v2.0/authorize" in url

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
            "scope": "Mail.Send User.Read offline_access",
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await provider.exchange_code("auth-code-123", "https://example.com/callback")

            assert result.access_token == "new-access-token"
            assert result.refresh_token == "new-refresh-token"
            assert result.expires_at is not None

    @pytest.mark.asyncio
    async def test_handle_callback_stores_tokens(self, provider, storage):
        """Should exchange code and store tokens."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.handle_callback(
                "user-123",
                OAuthCallbackParams(
                    code="auth-code",
                    redirect_uri="https://example.com/callback",
                ),
            )

            stored = await storage.get_token("user-123", "microsoft")
            assert stored is not None
            assert stored.access_token == "new-access-token"
            assert stored.refresh_token == "new-refresh-token"

    @pytest.mark.asyncio
    async def test_get_valid_token_returns_stored_if_not_expired(self, provider, storage):
        """Should return stored token if not expired."""
        future_date = datetime.now() + timedelta(hours=1)
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                refresh_token="refresh-token",
                expires_at=future_date,
            ),
        )

        token = await provider.get_valid_token("user-123")
        assert token == "valid-token"

    @pytest.mark.asyncio
    async def test_get_valid_token_refreshes_if_expired(self, provider, storage):
        """Should refresh token if expired."""
        past_date = datetime.now() - timedelta(hours=1)
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="expired-token",
                refresh_token="refresh-token",
                expires_at=past_date,
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            token = await provider.get_valid_token("user-123")
            assert token == "new-access-token"

    @pytest.mark.asyncio
    async def test_get_valid_token_throws_when_not_found(self, provider):
        """Should throw TokenNotFoundError when no token exists."""
        with pytest.raises(TokenNotFoundError):
            await provider.get_valid_token("user-123")

    @pytest.mark.asyncio
    async def test_get_connection_status_connected_with_refresh(self, provider, storage):
        """Should return connected=True with refresh token."""
        await storage.save_token(
            "user-123",
            "microsoft",
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
    async def test_get_connection_status_connected_without_refresh(self, provider, storage):
        """Should return connected=True without refresh token."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(access_token="token"),
        )

        status = await provider.get_connection_status("user-123")
        assert status.connected is True
        assert status.has_refresh_token is False

    @pytest.mark.asyncio
    async def test_get_connection_status_not_connected(self, provider):
        """Should return connected=False when no token."""
        status = await provider.get_connection_status("user-123")
        assert status.connected is False
        assert status.has_refresh_token is False

    @pytest.mark.asyncio
    async def test_disconnect_deletes_token(self, provider, storage):
        """Should delete stored token."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(access_token="token", refresh_token="refresh"),
        )

        # Microsoft doesn't have a revoke endpoint
        await provider.disconnect("user-123")

        token = await storage.get_token("user-123", "microsoft")
        assert token is None

    @pytest.mark.asyncio
    async def test_store_external_tokens(self, provider, storage):
        """Should store tokens from external source."""
        await provider.store_external_tokens(
            "user-123",
            TokenData(
                access_token="external-access",
                refresh_token="external-refresh",
                expires_at=datetime(2025, 6, 1),
            ),
        )

        token = await storage.get_token("user-123", "microsoft")
        assert token.access_token == "external-access"
        assert token.refresh_token == "external-refresh"

    @pytest.mark.asyncio
    async def test_send_email_success(self, provider, storage):
        """Should send email successfully."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.send_email(
                "user-123",
                MicrosoftSendEmailParams(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Hello World</p>",
                ),
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "https://graph.microsoft.com/v1.0/me/sendMail" in str(call_args)

    @pytest.mark.asyncio
    async def test_send_email_with_multiple_recipients(self, provider, storage):
        """Should send email with multiple recipients."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.send_email(
                "user-123",
                MicrosoftSendEmailParams(
                    to=["recipient1@example.com", "recipient2@example.com"],
                    subject="Test Subject",
                    body="<p>Hello World</p>",
                ),
            )

            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, provider, storage):
        """Should send email with cc and bcc."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.send_email(
                "user-123",
                MicrosoftSendEmailParams(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Hello World</p>",
                    cc="cc@example.com",
                    bcc="bcc@example.com",
                ),
            )

            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_plain_text(self, provider, storage):
        """Should send email with plain text content type."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.send_email(
                "user-123",
                MicrosoftSendEmailParams(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="Hello World",
                    content_type="Text",
                ),
            )

            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_throws_on_failure(self, provider, storage):
        """Should throw ProviderAPIError on failure."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 403
        mock_response.text = "Insufficient permissions"

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(ProviderAPIError):
                await provider.send_email(
                    "user-123",
                    MicrosoftSendEmailParams(
                        to="test@example.com",
                        subject="Test",
                        body="Body",
                    ),
                )

    @pytest.mark.asyncio
    async def test_send_email_throws_when_not_connected(self, provider):
        """Should throw TokenNotFoundError when not connected."""
        with pytest.raises(TokenNotFoundError):
            await provider.send_email(
                "user-123",
                MicrosoftSendEmailParams(
                    to="test@example.com",
                    subject="Test",
                    body="Body",
                ),
            )

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, provider, storage):
        """Should get user info successfully."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "user-ms-id",
            "displayName": "Test User",
            "mail": "test@example.com",
            "userPrincipalName": "test@example.com",
            "givenName": "Test",
            "surname": "User",
        }

        with patch.object(provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            user_info = await provider.get_user_info("user-123")

            assert user_info.id == "user-ms-id"
            assert user_info.display_name == "Test User"
            assert user_info.mail == "test@example.com"
            assert user_info.user_principal_name == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_info_throws_on_failure(self, provider, storage):
        """Should throw ProviderAPIError on failure."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            with pytest.raises(ProviderAPIError):
                await provider.get_user_info("user-123")

    @pytest.mark.asyncio
    async def test_get_user_info_throws_when_not_connected(self, provider):
        """Should throw TokenNotFoundError when not connected."""
        with pytest.raises(TokenNotFoundError):
            await provider.get_user_info("user-123")

    @pytest.mark.asyncio
    async def test_format_recipients_comma_separated(self, provider, storage):
        """Should handle comma-separated string recipients."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.send_email(
                "user-123",
                MicrosoftSendEmailParams(
                    to="user1@example.com, user2@example.com",
                    subject="Test",
                    body="Body",
                ),
            )

            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_format_recipients_semicolon_separated(self, provider, storage):
        """Should handle semicolon-separated string recipients."""
        await storage.save_token(
            "user-123",
            "microsoft",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.send_email(
                "user-123",
                MicrosoftSendEmailParams(
                    to="user1@example.com; user2@example.com",
                    subject="Test",
                    body="Body",
                ),
            )

            mock_post.assert_called_once()
