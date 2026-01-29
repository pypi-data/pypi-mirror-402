"""Tests for GoogleProvider."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nospoon_integrations.core.errors import ProviderAPIError, TokenNotFoundError
from nospoon_integrations.core.types import OAuthCallbackParams, ProviderConfig, TokenData
from nospoon_integrations.providers.google import (
    DraftEmailParams,
    GoogleProvider,
    SendEmailParams,
)
from nospoon_integrations.storage.memory import MemoryTokenStorage


class TestGoogleProvider:
    """Tests for the Google OAuth provider."""

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
            scopes=["https://www.googleapis.com/auth/gmail.compose"],
        )

    @pytest.fixture
    def provider(self, config, storage):
        """Create provider instance."""
        return GoogleProvider(config, storage)

    def test_get_auth_url_generates_correct_url(self, provider):
        """Should generate correct OAuth URL."""
        redirect_uri = "https://example.com/callback"
        url = provider.get_auth_url(redirect_uri)

        assert "accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url

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
            "scope": "https://www.googleapis.com/auth/gmail.compose",
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

            stored = await storage.get_token("user-123", "google")
            assert stored is not None
            assert stored.access_token == "new-access-token"
            assert stored.refresh_token == "new-refresh-token"

    @pytest.mark.asyncio
    async def test_get_valid_token_returns_stored_if_not_expired(self, provider, storage):
        """Should return stored token if not expired."""
        future_date = datetime.now() + timedelta(hours=1)
        await storage.save_token(
            "user-123",
            "google",
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
            "google",
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
            "google",
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
            "google",
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
            "google",
            TokenData(access_token="token", refresh_token="refresh"),
        )

        # Mock revoke endpoint
        mock_response = MagicMock()
        mock_response.is_success = True

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await provider.disconnect("user-123")

            token = await storage.get_token("user-123", "google")
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

        token = await storage.get_token("user-123", "google")
        assert token.access_token == "external-access"
        assert token.refresh_token == "external-refresh"

    @pytest.mark.asyncio
    async def test_create_draft_email_success(self, provider, storage):
        """Should create draft email successfully."""
        # Store a valid token
        await storage.save_token(
            "user-123",
            "google",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "draft-123",
            "message": {"id": "message-123", "threadId": "thread-123"},
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await provider.create_draft_email(
                "user-123",
                DraftEmailParams(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Hello World</p>",
                ),
            )

            assert result.id == "draft-123"

    @pytest.mark.asyncio
    async def test_create_draft_email_throws_on_failure(self, provider, storage):
        """Should throw ProviderAPIError on failure."""
        await storage.save_token(
            "user-123",
            "google",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(ProviderAPIError):
                await provider.create_draft_email(
                    "user-123",
                    DraftEmailParams(
                        to="test@example.com",
                        subject="Test",
                        body="Body",
                    ),
                )

    @pytest.mark.asyncio
    async def test_send_email_success(self, provider, storage):
        """Should send email successfully."""
        await storage.save_token(
            "user-123",
            "google",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "message-123",
            "threadId": "thread-123",
            "labelIds": ["SENT"],
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await provider.send_email(
                "user-123",
                SendEmailParams(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Hello World</p>",
                ),
            )

            assert result.id == "message-123"
            assert result.thread_id == "thread-123"
            assert "SENT" in result.label_ids

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc_reply_to(self, provider, storage):
        """Should send email with cc, bcc, and reply_to."""
        await storage.save_token(
            "user-123",
            "google",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "message-123",
            "threadId": "thread-123",
            "labelIds": ["SENT"],
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await provider.send_email(
                "user-123",
                SendEmailParams(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Hello World</p>",
                    cc="cc@example.com",
                    bcc="bcc@example.com",
                    reply_to="reply@example.com",
                ),
            )

            assert result.id == "message-123"

    @pytest.mark.asyncio
    async def test_send_email_as_reply_to_thread(self, provider, storage):
        """Should send email as reply to existing thread."""
        await storage.save_token(
            "user-123",
            "google",
            TokenData(
                access_token="valid-token",
                expires_at=datetime.now() + timedelta(hours=1),
            ),
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "message-456",
            "threadId": "existing-thread-123",
            "labelIds": ["SENT"],
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await provider.send_email(
                "user-123",
                SendEmailParams(
                    to="recipient@example.com",
                    subject="Re: Test Subject",
                    body="<p>Reply content</p>",
                    thread_id="existing-thread-123",
                ),
            )

            assert result.thread_id == "existing-thread-123"

    @pytest.mark.asyncio
    async def test_send_email_throws_on_failure(self, provider, storage):
        """Should throw ProviderAPIError on failure."""
        await storage.save_token(
            "user-123",
            "google",
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
                    SendEmailParams(
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
                SendEmailParams(
                    to="test@example.com",
                    subject="Test",
                    body="Body",
                ),
            )
