"""Tests for BaseProvider class."""

from urllib.parse import parse_qs, urlparse

import pytest

from nospoon_integrations.core.types import (
    ProviderConfig,
    ProviderEndpoints,
    TokenData,
)
from nospoon_integrations.providers.base_provider import (
    BaseProvider,
    SecureCallbackFailure,
)
from nospoon_integrations.storage.memory import MemoryTokenStorage


class ConcreteTestProvider(BaseProvider):
    """Concrete implementation of BaseProvider for testing."""

    def __init__(self, config: ProviderConfig, storage: MemoryTokenStorage):
        endpoints = ProviderEndpoints(
            auth_url="https://test.example.com/oauth/authorize",
            token_url="https://test.example.com/oauth/token",
            revoke_url="https://test.example.com/oauth/revoke",
        )
        super().__init__("test", endpoints, config, storage)


class TestScopeValidationMethods:
    """Tests for scope validation methods."""

    @pytest.fixture
    def storage(self):
        return MemoryTokenStorage()

    @pytest.fixture
    def provider(self, storage):
        return ConcreteTestProvider(
            ProviderConfig(
                client_id="test-client-id",
                client_secret="test-client-secret",
                scopes=["read", "write"],
            ),
            storage,
        )

    @pytest.mark.asyncio
    async def test_has_required_scopes_returns_true_when_all_granted(
        self,
        provider,
        storage,
    ):
        """Should return true when all required scopes are granted."""
        await storage.save_tokens(
            "user-123",
            "test",
            TokenData(access_token="access-token", scope="read write admin"),
        )

        result = await provider.has_required_scopes("user-123", ["read", "write"])

        assert result is True

    @pytest.mark.asyncio
    async def test_has_required_scopes_returns_false_when_missing(
        self,
        provider,
        storage,
    ):
        """Should return false when some scopes are missing."""
        await storage.save_tokens(
            "user-123",
            "test",
            TokenData(access_token="access-token", scope="read"),
        )

        result = await provider.has_required_scopes("user-123", ["read", "write"])

        assert result is False

    @pytest.mark.asyncio
    async def test_has_required_scopes_returns_false_when_no_tokens(self, provider):
        """Should return false when no tokens exist."""
        result = await provider.has_required_scopes("user-123", ["read"])

        assert result is False

    @pytest.mark.asyncio
    async def test_has_required_scopes_returns_false_when_no_scope_stored(
        self,
        provider,
        storage,
    ):
        """Should return false when no scope is stored."""
        await storage.save_tokens(
            "user-123",
            "test",
            TokenData(access_token="access-token"),
        )

        result = await provider.has_required_scopes("user-123", ["read"])

        assert result is False

    @pytest.mark.asyncio
    async def test_get_missing_scopes_returns_empty_when_all_granted(
        self,
        provider,
        storage,
    ):
        """Should return empty list when all scopes are granted."""
        await storage.save_tokens(
            "user-123",
            "test",
            TokenData(access_token="access-token", scope="read write admin"),
        )

        result = await provider.get_missing_scopes("user-123", ["read", "write"])

        assert result == []

    @pytest.mark.asyncio
    async def test_get_missing_scopes_returns_missing(self, provider, storage):
        """Should return missing scopes."""
        await storage.save_tokens(
            "user-123",
            "test",
            TokenData(access_token="access-token", scope="read"),
        )

        result = await provider.get_missing_scopes(
            "user-123",
            ["read", "write", "delete"],
        )

        assert result == ["write", "delete"]

    @pytest.mark.asyncio
    async def test_get_missing_scopes_returns_all_when_no_tokens(self, provider):
        """Should return all scopes when no tokens exist."""
        result = await provider.get_missing_scopes("user-123", ["read", "write"])

        assert result == ["read", "write"]

    @pytest.mark.asyncio
    async def test_get_granted_scopes_returns_all_granted(self, provider, storage):
        """Should return all granted scopes."""
        await storage.save_tokens(
            "user-123",
            "test",
            TokenData(access_token="access-token", scope="read write admin"),
        )

        result = await provider.get_granted_scopes("user-123")

        assert result == ["read", "write", "admin"]

    @pytest.mark.asyncio
    async def test_get_granted_scopes_returns_empty_when_no_tokens(self, provider):
        """Should return empty list when no tokens exist."""
        result = await provider.get_granted_scopes("user-123")

        assert result == []


class TestSecureOAuthFlowMethods:
    """Tests for secure OAuth flow methods."""

    @pytest.fixture
    def storage(self):
        return MemoryTokenStorage()

    @pytest.fixture
    def provider(self, storage):
        return ConcreteTestProvider(
            ProviderConfig(
                client_id="test-client-id",
                client_secret="test-client-secret",
                scopes=["read", "write"],
            ),
            storage,
        )

    def test_generate_secure_auth_url_creates_url_with_state(self, provider):
        """Should generate URL with signed state token."""
        url = provider.generate_secure_auth_url(
            "user-123",
            "https://myapp.com/callback",
            "test-secret",
        )

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "test.example.com" in url
        assert "state" in params
        assert "client_id" in params
        assert params["client_id"][0] == "test-client-id"

    def test_generate_secure_auth_url_includes_additional_params(self, provider):
        """Should include additional params."""
        url = provider.generate_secure_auth_url(
            "user-123",
            "https://myapp.com/callback",
            "test-secret",
            {"access_type": "offline", "prompt": "consent"},
        )

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert params["access_type"][0] == "offline"
        assert params["prompt"][0] == "consent"

    def test_generate_secure_auth_url_creates_unique_urls(self, provider):
        """Should generate unique URLs due to state nonce."""
        url1 = provider.generate_secure_auth_url(
            "user-123",
            "https://myapp.com/callback",
            "test-secret",
        )
        url2 = provider.generate_secure_auth_url(
            "user-123",
            "https://myapp.com/callback",
            "test-secret",
        )

        params1 = parse_qs(urlparse(url1).query)
        params2 = parse_qs(urlparse(url2).query)

        assert params1["state"][0] != params2["state"][0]

    @pytest.mark.asyncio
    async def test_handle_secure_callback_returns_failure_for_invalid_state(
        self,
        provider,
    ):
        """Should return failure for invalid state token."""
        result = await provider.handle_secure_callback(
            "auth-code",
            "invalid-state",
            "https://myapp.com/callback",
            "test-secret",
        )

        assert result.success is False
        assert isinstance(result, SecureCallbackFailure)
        assert "Invalid state token format" in result.error

    @pytest.mark.asyncio
    async def test_handle_secure_callback_returns_failure_for_wrong_secret(
        self,
        provider,
    ):
        """Should return failure for state with wrong secret."""
        # Generate state with one secret
        url = provider.generate_secure_auth_url(
            "user-123",
            "https://myapp.com/callback",
            "test-secret",
        )
        params = parse_qs(urlparse(url).query)
        state = params["state"][0]

        # Try to verify with different secret
        result = await provider.handle_secure_callback(
            "auth-code",
            state,
            "https://myapp.com/callback",
            "wrong-secret",
        )

        assert result.success is False
        assert isinstance(result, SecureCallbackFailure)
        assert "Invalid signature" in result.error
