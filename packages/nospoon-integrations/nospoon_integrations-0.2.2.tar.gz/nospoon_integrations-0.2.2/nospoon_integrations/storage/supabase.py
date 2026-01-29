"""Supabase token storage implementation."""

from datetime import datetime
from typing import Any, Optional

from nospoon_integrations.core.types import TokenData


class SupabaseTokenStorage:
    """
    Token storage using Supabase.

    Expects a table with the following columns:
    - user_id (or custom)
    - provider (or custom)
    - access_token
    - refresh_token
    - expires_at
    - scope
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        table_name: str = "user_integrations",
        user_id_column: str = "user_id",
        provider_column: str = "provider",
    ) -> None:
        try:
            from supabase import create_client
        except ImportError:
            raise ImportError(
                "supabase package is required for SupabaseTokenStorage. "
                "Install it with: pip install nospoon-integrations[supabase]"
            ) from None

        self._client = create_client(supabase_url, supabase_key)
        self._table_name = table_name
        self._user_id_column = user_id_column
        self._provider_column = provider_column

    async def get_tokens(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Get tokens for a user and provider."""
        result = (
            self._client.table(self._table_name)
            .select("access_token, refresh_token, expires_at, scope")
            .eq(self._user_id_column, user_id)
            .eq(self._provider_column, provider)
            .single()
            .execute()
        )

        if not result.data:
            return None

        data: dict[str, Any] = result.data
        return TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token") or None,
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
            scope=data.get("scope"),
        )

    async def save_tokens(self, user_id: str, provider: str, tokens: TokenData) -> None:
        """Save tokens for a user and provider."""
        token_record = {
            self._user_id_column: user_id,
            self._provider_column: provider,
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token or "",
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
            "scope": tokens.scope,
        }

        # Check if exists
        existing = (
            self._client.table(self._table_name)
            .select("id")
            .eq(self._user_id_column, user_id)
            .eq(self._provider_column, provider)
            .single()
            .execute()
        )

        if existing.data:
            # Update
            self._client.table(self._table_name).update(
                {
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token or "",
                    "expires_at": (tokens.expires_at.isoformat() if tokens.expires_at else None),
                    "scope": tokens.scope,
                }
            ).eq(self._user_id_column, user_id).eq(self._provider_column, provider).execute()
        else:
            # Insert
            self._client.table(self._table_name).insert(token_record).execute()

    async def delete_tokens(self, user_id: str, provider: str) -> None:
        """Delete tokens for a user and provider."""
        self._client.table(self._table_name).delete().eq(self._user_id_column, user_id).eq(
            self._provider_column, provider
        ).execute()

    async def has_tokens(self, user_id: str, provider: str) -> bool:
        """Check if tokens exist for a user and provider."""
        result = (
            self._client.table(self._table_name)
            .select("id")
            .eq(self._user_id_column, user_id)
            .eq(self._provider_column, provider)
            .single()
            .execute()
        )
        return bool(result.data)
