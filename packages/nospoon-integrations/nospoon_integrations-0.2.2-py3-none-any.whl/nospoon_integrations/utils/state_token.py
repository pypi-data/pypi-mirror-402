"""
OAuth state token utilities for CSRF protection.

State tokens are signed with HMAC-SHA256 to prevent tampering and include:
- User ID: Links the OAuth flow to a specific user
- Timestamp: Allows expiration checking
- Nonce: Prevents replay attacks
"""

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StateTokenPayload:
    """Payload contained in a state token."""

    user_id: str
    timestamp: float
    nonce: str


@dataclass
class StateTokenOptions:
    """Options for state token creation and verification."""

    max_age_ms: int = field(default=10 * 60 * 1000)  # 10 minutes


@dataclass
class StateTokenVerifyResult:
    """Result from verifying a state token."""

    valid: bool
    user_id: Optional[str] = None
    error: Optional[str] = None


def _generate_nonce() -> str:
    """Generate a cryptographically random UUID."""
    return str(uuid.uuid4())


def _sign_payload(payload_base64: str, secret: str) -> str:
    """Create HMAC-SHA256 signature of the payload."""
    signature = hmac.new(
        secret.encode("utf-8"),
        payload_base64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(signature).decode("utf-8")


def _verify_signature(payload_base64: str, signature_base64: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected_signature = _sign_payload(payload_base64, secret)
    return hmac.compare_digest(expected_signature, signature_base64)


def create_state_token(user_id: str, secret: str) -> str:
    """
    Create a signed state token for OAuth CSRF protection.

    The token contains:
    - User ID
    - Timestamp (for expiration)
    - Random nonce (for replay protection)

    The payload is signed with HMAC-SHA256 using the provided secret.

    Args:
        user_id: The user ID to embed in the token
        secret: Secret key for signing (use a secure random string)

    Returns:
        Base64-encoded signed token in format: payload.signature

    Raises:
        ValueError: If user_id or secret is empty

    Example:
        ```python
        state = create_state_token(user_id, os.environ["OAUTH_STATE_SECRET"])
        auth_url = provider.get_auth_url(redirect_uri, state=state)
        ```
    """
    if not user_id:
        raise ValueError("user_id is required for state token")
    if not secret:
        raise ValueError("secret is required for state token signing")

    payload = StateTokenPayload(
        user_id=user_id,
        timestamp=time.time() * 1000,  # Convert to milliseconds
        nonce=_generate_nonce(),
    )

    payload_dict = {
        "userId": payload.user_id,
        "timestamp": payload.timestamp,
        "nonce": payload.nonce,
    }

    payload_json = json.dumps(payload_dict)
    payload_base64 = base64.b64encode(payload_json.encode("utf-8")).decode("utf-8")

    signature_base64 = _sign_payload(payload_base64, secret)

    return f"{payload_base64}.{signature_base64}"


def verify_state_token(
    state: str,
    secret: str,
    options: Optional[StateTokenOptions] = None,
) -> StateTokenVerifyResult:
    """
    Verify and decode a state token.

    Checks:
    1. Token format is valid
    2. HMAC signature is valid
    3. Token has not expired

    Args:
        state: The state token to verify
        secret: Secret key used for signing
        options: Verification options (optional)

    Returns:
        Verification result with user_id if valid

    Example:
        ```python
        result = verify_state_token(state, os.environ["OAUTH_STATE_SECRET"])
        if result.valid:
            print(f"User ID: {result.user_id}")
        else:
            print(f"Invalid state: {result.error}")
        ```
    """
    if not state:
        return StateTokenVerifyResult(valid=False, error="State token is required")
    if not secret:
        return StateTokenVerifyResult(valid=False, error="Secret is required for verification")

    opts = options or StateTokenOptions()

    try:
        parts = state.split(".")
        if len(parts) != 2:
            return StateTokenVerifyResult(valid=False, error="Invalid state token format")

        payload_base64, signature_base64 = parts

        # Verify HMAC signature
        if not _verify_signature(payload_base64, signature_base64, secret):
            return StateTokenVerifyResult(valid=False, error="Invalid signature")

        # Decode and parse payload
        payload_json = base64.b64decode(payload_base64).decode("utf-8")
        payload_dict = json.loads(payload_json)

        # Check expiration
        current_time_ms = time.time() * 1000
        if current_time_ms - payload_dict["timestamp"] > opts.max_age_ms:
            return StateTokenVerifyResult(valid=False, error="State token expired")

        return StateTokenVerifyResult(valid=True, user_id=payload_dict["userId"])

    except Exception as e:
        return StateTokenVerifyResult(
            valid=False,
            error=f"Failed to verify state token: {e!s}",
        )


def extract_user_id_from_state(state: str) -> Optional[str]:
    """
    Extract the user ID from a state token without full verification.

    Useful for logging/debugging - do NOT use for authentication.

    Args:
        state: The state token

    Returns:
        The user ID or None if parsing fails
    """
    try:
        parts = state.split(".")
        if not parts:
            return None

        payload_base64 = parts[0]
        payload_json = base64.b64decode(payload_base64).decode("utf-8")
        payload_dict = json.loads(payload_json)

        user_id: Optional[str] = payload_dict.get("userId")
        return user_id
    except Exception:
        return None
