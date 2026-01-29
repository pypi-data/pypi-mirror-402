"""Tests for MemoryTokenStorage."""

from datetime import datetime

import pytest

from nospoon_integrations.core.types import TokenData
from nospoon_integrations.storage.memory import MemoryTokenStorage


class TestMemoryTokenStorage:
    """Tests for the in-memory token storage implementation."""

    @pytest.fixture
    def storage(self):
        """Create a fresh storage instance for each test."""
        return MemoryTokenStorage()

    @pytest.mark.asyncio
    async def test_get_token_returns_none_for_nonexistent(self, storage):
        """Should return None when no token exists."""
        token = await storage.get_token("user-123", "google")
        assert token is None

    @pytest.mark.asyncio
    async def test_get_token_returns_stored_token(self, storage):
        """Should return the stored token."""
        token_data = TokenData(
            access_token="access-token-123",
            refresh_token="refresh-token-456",
            expires_at=datetime(2025, 1, 1),
        )
        await storage.save_token("user-123", "google", token_data)

        retrieved = await storage.get_token("user-123", "google")

        assert retrieved is not None
        assert retrieved.access_token == "access-token-123"
        assert retrieved.refresh_token == "refresh-token-456"
        assert retrieved.expires_at == datetime(2025, 1, 1)

    @pytest.mark.asyncio
    async def test_tokens_isolated_by_user(self, storage):
        """Should keep tokens separate per user."""
        token1 = TokenData(access_token="token-1")
        token2 = TokenData(access_token="token-2")

        await storage.save_token("user-1", "google", token1)
        await storage.save_token("user-2", "google", token2)

        retrieved1 = await storage.get_token("user-1", "google")
        retrieved2 = await storage.get_token("user-2", "google")

        assert retrieved1.access_token == "token-1"
        assert retrieved2.access_token == "token-2"

    @pytest.mark.asyncio
    async def test_tokens_isolated_by_provider(self, storage):
        """Should keep tokens separate per provider."""
        google_token = TokenData(access_token="google-token")
        hubspot_token = TokenData(access_token="hubspot-token")

        await storage.save_token("user-1", "google", google_token)
        await storage.save_token("user-1", "hubspot", hubspot_token)

        retrieved_google = await storage.get_token("user-1", "google")
        retrieved_hubspot = await storage.get_token("user-1", "hubspot")

        assert retrieved_google.access_token == "google-token"
        assert retrieved_hubspot.access_token == "hubspot-token"

    @pytest.mark.asyncio
    async def test_save_token_without_optional_fields(self, storage):
        """Should save token without optional fields."""
        token_data = TokenData(access_token="access-token")

        await storage.save_token("user-123", "google", token_data)
        retrieved = await storage.get_token("user-123", "google")

        assert retrieved.access_token == "access-token"
        assert retrieved.refresh_token is None
        assert retrieved.expires_at is None

    @pytest.mark.asyncio
    async def test_save_token_overwrites_existing(self, storage):
        """Should overwrite existing token on save."""
        old_token = TokenData(access_token="old-token")
        new_token = TokenData(access_token="new-token")

        await storage.save_token("user-123", "google", old_token)
        await storage.save_token("user-123", "google", new_token)

        retrieved = await storage.get_token("user-123", "google")
        assert retrieved.access_token == "new-token"

    @pytest.mark.asyncio
    async def test_delete_token_removes_existing(self, storage):
        """Should delete an existing token."""
        token_data = TokenData(access_token="token")
        await storage.save_token("user-123", "google", token_data)

        await storage.delete_token("user-123", "google")

        retrieved = await storage.get_token("user-123", "google")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_token_no_error_for_nonexistent(self, storage):
        """Should not raise error when deleting non-existent token."""
        # Should not raise
        await storage.delete_token("user-123", "google")

    @pytest.mark.asyncio
    async def test_delete_token_only_deletes_specified_provider(self, storage):
        """Should only delete the specified provider's token."""
        google_token = TokenData(access_token="google")
        hubspot_token = TokenData(access_token="hubspot")

        await storage.save_token("user-123", "google", google_token)
        await storage.save_token("user-123", "hubspot", hubspot_token)

        await storage.delete_token("user-123", "google")

        assert await storage.get_token("user-123", "google") is None
        assert await storage.get_token("user-123", "hubspot") is not None

    def test_clear_removes_all_tokens(self, storage):
        """Should clear all tokens from storage."""
        # Use sync save for this test since clear is synchronous
        import asyncio

        async def setup():
            await storage.save_token("user-1", "google", TokenData(access_token="1"))
            await storage.save_token("user-2", "hubspot", TokenData(access_token="2"))

        asyncio.get_event_loop().run_until_complete(setup())

        storage.clear()

        async def verify():
            assert await storage.get_token("user-1", "google") is None
            assert await storage.get_token("user-2", "hubspot") is None

        asyncio.get_event_loop().run_until_complete(verify())
