"""Google OAuth provider with Gmail API support."""

import base64
import json
from dataclasses import dataclass
from typing import Any, Optional

from nospoon_integrations.core.errors import ProviderAPIError
from nospoon_integrations.core.types import (
    ProviderConfig,
    ProviderEndpoints,
    TokenStorage,
)
from nospoon_integrations.providers.base_provider import BaseProvider

GOOGLE_ENDPOINTS = ProviderEndpoints(
    auth_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    revoke_url="https://oauth2.googleapis.com/revoke",
    user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
)

# ============ Gmail API Scopes ============

# Gmail API scope for sending emails only.
# Most restrictive - cannot read or create drafts.
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"

# Gmail API scope for creating drafts and sending emails.
# Cannot read existing emails.
GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"

# Gmail API scope for read-only access to emails.
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

# Gmail API scope for full read/write access (except permanent deletion).
GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"

# Gmail API scope for full access including permanent deletion.
GMAIL_FULL_ACCESS_SCOPE = "https://mail.google.com/"

# Google user profile scope (email).
GOOGLE_USERINFO_EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email"

# Google user profile scope (profile).
GOOGLE_USERINFO_PROFILE_SCOPE = "https://www.googleapis.com/auth/userinfo.profile"


@dataclass
class DraftEmailParams:
    """Parameters for creating a draft email."""

    to: str
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None


@dataclass
class DraftEmailResult:
    """Result from creating a draft email."""

    id: str
    message_id: str
    thread_id: str


@dataclass
class SendEmailParams:
    """Parameters for sending an email."""

    to: str
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None


@dataclass
class SendEmailResult:
    """Result from sending an email."""

    id: str
    thread_id: str
    label_ids: list[str]


@dataclass
class GoogleUserInfo:
    """Google user info."""

    id: str
    email: str
    name: str
    picture: Optional[str] = None


class GoogleProvider(BaseProvider):
    """Google OAuth provider with Gmail API support."""

    def __init__(self, config: ProviderConfig, storage: TokenStorage) -> None:
        super().__init__("google", GOOGLE_ENDPOINTS, config, storage)

    def _get_token_request_headers(self) -> dict[str, str]:
        """Override to use JSON content type for Google."""
        return {"Content-Type": "application/json"}

    def _get_token_request_body(self, code: str, redirect_uri: str) -> str:
        """Override to use JSON body for Google."""
        return json.dumps(
            {
                "grant_type": "authorization_code",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            }
        )

    def _get_refresh_token_request_body(self, refresh_token: str) -> str:
        """Override to use JSON body for Google refresh."""
        return json.dumps(
            {
                "grant_type": "refresh_token",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "refresh_token": refresh_token,
            }
        )

    def get_auth_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        additional_params: Optional[dict[str, str]] = None,
    ) -> str:
        """Override auth URL to include access_type=offline for refresh token."""
        params = additional_params or {}
        params.update(
            {
                "access_type": "offline",
                "prompt": "consent",
            }
        )
        return super().get_auth_url(redirect_uri, state, params)

    # Google-specific API methods

    async def create_draft_email(self, user_id: str, params: DraftEmailParams) -> DraftEmailResult:
        """
        Create a draft email in Gmail.

        Args:
            user_id: User ID
            params: Draft email parameters

        Returns:
            Draft email result
        """
        access_token = await self.get_valid_token(user_id)

        email_lines = [f"To: {params.to}"]
        if params.cc:
            email_lines.append(f"Cc: {params.cc}")
        if params.bcc:
            email_lines.append(f"Bcc: {params.bcc}")
        email_lines.extend(
            [
                f"Subject: {params.subject}",
                "Content-Type: text/html; charset=utf-8",
                "",
                params.body,
            ]
        )

        email_content = "\r\n".join(email_lines)
        encoded_email = self._base64_url_encode(email_content)

        response = await self._client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"message": {"raw": encoded_email}},
        )

        if not response.is_success:
            raise ProviderAPIError(
                "google",
                response.status_code,
                "Failed to create draft email",
                response.text,
            )

        data: dict[str, Any] = response.json()
        return DraftEmailResult(
            id=data["id"],
            message_id=data["message"]["id"],
            thread_id=data["message"]["threadId"],
        )

    async def send_email(self, user_id: str, params: SendEmailParams) -> SendEmailResult:
        """
        Send an email via Gmail.

        Requires one of the following scopes:
        - gmail.send (most restrictive, send-only)
        - gmail.compose (create drafts + send)
        - gmail.modify (full read/write access)

        Args:
            user_id: User ID
            params: Email parameters

        Returns:
            Send email result with message ID and thread ID

        Example:
            ```python
            result = await google.send_email(user_id, SendEmailParams(
                to="recipient@example.com",
                subject="Hello",
                body="<p>Hello World!</p>",
            ))
            print(f"Sent message ID: {result.id}")
            ```
        """
        access_token = await self.get_valid_token(user_id)

        email_lines = [f"To: {params.to}"]
        if params.cc:
            email_lines.append(f"Cc: {params.cc}")
        if params.bcc:
            email_lines.append(f"Bcc: {params.bcc}")
        if params.reply_to:
            email_lines.append(f"Reply-To: {params.reply_to}")
        email_lines.extend(
            [
                f"Subject: {params.subject}",
                "Content-Type: text/html; charset=utf-8",
                "",
                params.body,
            ]
        )

        email_content = "\r\n".join(email_lines)
        encoded_email = self._base64_url_encode(email_content)

        request_body: dict[str, Any] = {"raw": encoded_email}
        if params.thread_id:
            request_body["threadId"] = params.thread_id

        response = await self._client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=request_body,
        )

        if not response.is_success:
            raise ProviderAPIError(
                "google",
                response.status_code,
                "Failed to send email",
                response.text,
            )

        data: dict[str, Any] = response.json()
        return SendEmailResult(
            id=data["id"],
            thread_id=data["threadId"],
            label_ids=data.get("labelIds", []),
        )

    async def get_user_info(self, user_id: str) -> GoogleUserInfo:
        """
        Get user info from Google.

        Args:
            user_id: User ID

        Returns:
            Google user info
        """
        access_token = await self.get_valid_token(user_id)

        response = await self._client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if not response.is_success:
            raise ProviderAPIError(
                "google",
                response.status_code,
                "Failed to get user info",
                response.text,
            )

        data: dict[str, Any] = response.json()
        return GoogleUserInfo(
            id=data["id"],
            email=data["email"],
            name=data["name"],
            picture=data.get("picture"),
        )

    @staticmethod
    def _base64_url_encode(data: str) -> str:
        """URL-safe base64 encoding for Gmail API."""
        encoded = base64.urlsafe_b64encode(data.encode("utf-8"))
        return encoded.decode("utf-8").rstrip("=")
