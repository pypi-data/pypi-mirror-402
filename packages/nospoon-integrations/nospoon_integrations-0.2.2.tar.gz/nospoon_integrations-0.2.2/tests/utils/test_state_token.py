"""Tests for state token utilities."""

import pytest

from nospoon_integrations.utils.state_token import (
    StateTokenOptions,
    create_state_token,
    extract_user_id_from_state,
    verify_state_token,
)


class TestCreateStateToken:
    """Tests for create_state_token function."""

    def test_creates_valid_state_token(self):
        """Should create a valid state token."""
        token = create_state_token("user-12345", "test-secret")

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 2  # payload.signature format

    def test_raises_error_if_user_id_is_empty(self):
        """Should raise error if userId is empty."""
        with pytest.raises(ValueError, match="user_id is required"):
            create_state_token("", "test-secret")

    def test_raises_error_if_secret_is_empty(self):
        """Should raise error if secret is empty."""
        with pytest.raises(ValueError, match="secret is required"):
            create_state_token("user-12345", "")

    def test_generates_unique_tokens_due_to_nonce(self):
        """Should generate unique tokens due to nonce."""
        token1 = create_state_token("user-12345", "test-secret")
        token2 = create_state_token("user-12345", "test-secret")

        assert token1 != token2


class TestVerifyStateToken:
    """Tests for verify_state_token function."""

    def test_verifies_valid_token(self):
        """Should verify a valid token."""
        token = create_state_token("user-12345", "test-secret")
        result = verify_state_token(token, "test-secret")

        assert result.valid is True
        assert result.user_id == "user-12345"
        assert result.error is None

    def test_rejects_token_with_wrong_secret(self):
        """Should reject token with wrong secret."""
        token = create_state_token("user-12345", "test-secret")
        result = verify_state_token(token, "wrong-secret")

        assert result.valid is False
        assert result.error == "Invalid signature"

    def test_rejects_tampered_token(self):
        """Should reject tampered token."""
        token = create_state_token("user-12345", "test-secret")
        payload, signature = token.split(".")
        tampered_token = f"{payload}x.{signature}"

        result = verify_state_token(tampered_token, "test-secret")

        assert result.valid is False
        assert result.error == "Invalid signature"

    def test_rejects_token_with_invalid_format(self):
        """Should reject token with invalid format."""
        result = verify_state_token("invalid-token", "test-secret")

        assert result.valid is False
        assert result.error == "Invalid state token format"

    def test_rejects_empty_token(self):
        """Should reject empty token."""
        result = verify_state_token("", "test-secret")

        assert result.valid is False
        assert result.error == "State token is required"

    def test_rejects_if_secret_is_empty(self):
        """Should reject if secret is empty."""
        token = create_state_token("user-12345", "test-secret")
        result = verify_state_token(token, "")

        assert result.valid is False
        assert result.error == "Secret is required for verification"

    def test_rejects_expired_token(self):
        """Should reject expired token."""
        token = create_state_token("user-12345", "test-secret")

        # Wait a short time to ensure the token is older than our max age
        import time as time_module

        time_module.sleep(0.015)  # 15ms

        # Verify with a very short max age to simulate expiration
        result = verify_state_token(
            token,
            "test-secret",
            StateTokenOptions(max_age_ms=5),  # 5ms - token is older
        )

        assert result.valid is False
        assert result.error == "State token expired"

    def test_accepts_valid_token_within_max_age(self):
        """Should accept valid token within max age."""
        token = create_state_token("user-12345", "test-secret")

        result = verify_state_token(
            token,
            "test-secret",
            StateTokenOptions(max_age_ms=60 * 60 * 1000),  # 1 hour
        )

        assert result.valid is True
        assert result.user_id == "user-12345"


class TestExtractUserIdFromState:
    """Tests for extract_user_id_from_state function."""

    def test_extracts_user_id_from_valid_token(self):
        """Should extract userId from valid token."""
        token = create_state_token("user-12345", "test-secret")
        extracted_user_id = extract_user_id_from_state(token)

        assert extracted_user_id == "user-12345"

    def test_returns_none_for_invalid_token(self):
        """Should return None for invalid token."""
        extracted_user_id = extract_user_id_from_state("invalid-token")

        assert extracted_user_id is None

    def test_returns_none_for_empty_token(self):
        """Should return None for empty token."""
        extracted_user_id = extract_user_id_from_state("")

        assert extracted_user_id is None

    def test_returns_none_for_malformed_base64(self):
        """Should return None for malformed base64."""
        extracted_user_id = extract_user_id_from_state("!!!invalid!!!.signature")

        assert extracted_user_id is None


class TestEndToEndFlow:
    """End-to-end tests for state token flow."""

    def test_complete_oauth_state_flow(self):
        """Should work for complete OAuth state flow."""
        user_id = "user-12345"
        secret = "test-secret"

        # 1. Generate secure auth URL (create state)
        state = create_state_token(user_id, secret)

        # 2. User goes through OAuth flow...
        # 3. On callback, verify state
        result = verify_state_token(state, secret)

        assert result.valid is True
        assert result.user_id == user_id
