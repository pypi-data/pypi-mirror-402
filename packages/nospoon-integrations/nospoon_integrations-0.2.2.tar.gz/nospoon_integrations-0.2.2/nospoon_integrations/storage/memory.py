"""In-memory token storage for testing."""

from typing import Optional

from nospoon_integrations.core.types import TokenData


class MemoryTokenStorage:
    """
    In-memory token storage implementation.
    Useful for testing and development.
    """

    def __init__(self) -> None:
        self._tokens: dict[str, TokenData] = {}

    def _get_key(self, user_id: str, provider: str) -> str:
        return f"{user_id}:{provider}"

    async def get_tokens(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Get tokens for a user and provider."""
        key = self._get_key(user_id, provider)
        return self._tokens.get(key)

    async def save_tokens(self, user_id: str, provider: str, tokens: TokenData) -> None:
        """Save tokens for a user and provider."""
        key = self._get_key(user_id, provider)
        self._tokens[key] = tokens

    async def delete_tokens(self, user_id: str, provider: str) -> None:
        """Delete tokens for a user and provider."""
        key = self._get_key(user_id, provider)
        self._tokens.pop(key, None)

    async def has_tokens(self, user_id: str, provider: str) -> bool:
        """Check if tokens exist for a user and provider."""
        key = self._get_key(user_id, provider)
        return key in self._tokens

    # Alias methods for convenience
    async def get_token(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Alias for get_tokens."""
        return await self.get_tokens(user_id, provider)

    async def save_token(self, user_id: str, provider: str, tokens: TokenData) -> None:
        """Alias for save_tokens."""
        await self.save_tokens(user_id, provider, tokens)

    async def delete_token(self, user_id: str, provider: str) -> None:
        """Alias for delete_tokens."""
        await self.delete_tokens(user_id, provider)

    def clear(self) -> None:
        """Clear all stored tokens. Useful for test cleanup."""
        self._tokens.clear()

    def get_all(self) -> dict[str, TokenData]:
        """Get all stored tokens. Useful for debugging."""
        return dict(self._tokens)
