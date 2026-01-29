"""Microsoft OAuth provider with Outlook/Microsoft Graph API support."""

from dataclasses import dataclass
from typing import Any, Optional, Union

from nospoon_integrations.core.errors import ProviderAPIError
from nospoon_integrations.core.types import (
    ProviderConfig,
    ProviderEndpoints,
    TokenStorage,
)
from nospoon_integrations.providers.base_provider import BaseProvider

# Default endpoints using /common for multi-tenant support
MICROSOFT_ENDPOINTS = ProviderEndpoints(
    auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
    revoke_url=None,  # Microsoft doesn't have a simple revoke endpoint
    user_info_url="https://graph.microsoft.com/v1.0/me",
)

# ============ Microsoft Graph API Scopes ============

# Microsoft Graph API scope for sending emails.
MICROSOFT_MAIL_SEND_SCOPE = "Mail.Send"

# Microsoft Graph API scope for reading emails.
MICROSOFT_MAIL_READ_SCOPE = "Mail.Read"

# Microsoft Graph API scope for reading and writing emails.
MICROSOFT_MAIL_READWRITE_SCOPE = "Mail.ReadWrite"

# Microsoft Graph API scope for reading user profile.
MICROSOFT_USER_READ_SCOPE = "User.Read"

# Microsoft scope for getting refresh tokens (offline access).
MICROSOFT_OFFLINE_ACCESS_SCOPE = "offline_access"

# OpenID Connect scope for basic profile info.
MICROSOFT_OPENID_SCOPE = "openid"

# OpenID Connect scope for user profile.
MICROSOFT_PROFILE_SCOPE = "profile"

# OpenID Connect scope for user email.
MICROSOFT_EMAIL_SCOPE = "email"


@dataclass
class MicrosoftSendEmailParams:
    """Parameters for sending an email via Microsoft Graph."""

    to: Union[str, list[str]]
    subject: str
    body: str
    content_type: str = "HTML"  # 'HTML' or 'Text'
    cc: Optional[Union[str, list[str]]] = None
    bcc: Optional[Union[str, list[str]]] = None
    save_to_sent_items: bool = True


@dataclass
class MicrosoftUserInfo:
    """Microsoft user info from Graph API."""

    id: str
    display_name: str
    user_principal_name: str
    mail: Optional[str] = None
    given_name: Optional[str] = None
    surname: Optional[str] = None


class MicrosoftProvider(BaseProvider):
    """Microsoft OAuth provider with Outlook/Microsoft Graph API support."""

    def __init__(
        self,
        config: ProviderConfig,
        storage: TokenStorage,
        tenant: str = "common",
    ) -> None:
        """
        Initialize the Microsoft provider.

        Args:
            config: Provider configuration
            storage: Token storage implementation
            tenant: Azure AD tenant. Use 'common' for multi-tenant (default),
                    'organizations' for work/school only, 'consumers' for
                    personal accounts only, or a specific tenant ID.
        """
        # Override endpoints with tenant-specific URLs
        endpoints = ProviderEndpoints(
            auth_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
            token_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            revoke_url=None,
            user_info_url="https://graph.microsoft.com/v1.0/me",
        )
        super().__init__("microsoft", endpoints, config, storage)

    def get_auth_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        additional_params: Optional[dict[str, str]] = None,
    ) -> str:
        """Override auth URL to include response_mode and prompt for consent."""
        params = additional_params or {}
        params.update(
            {
                "response_mode": "query",
                "prompt": "consent",  # Always show consent to get refresh token
            }
        )
        return super().get_auth_url(redirect_uri, state, params)

    # ============ Microsoft-specific API methods ============

    async def send_email(self, user_id: str, params: MicrosoftSendEmailParams) -> None:
        """
        Send an email via Microsoft Graph API.

        Requires the Mail.Send scope.

        Args:
            user_id: User ID
            params: Email parameters

        Example:
            ```python
            await microsoft.send_email(user_id, MicrosoftSendEmailParams(
                to="recipient@example.com",
                subject="Hello",
                body="<p>Hello World!</p>",
            ))
            ```
        """
        access_token = await self.get_valid_token(user_id)

        # Format recipients
        to_recipients = self._format_recipients(params.to)
        cc_recipients = self._format_recipients(params.cc) if params.cc else None
        bcc_recipients = self._format_recipients(params.bcc) if params.bcc else None

        request_body: dict[str, Any] = {
            "message": {
                "subject": params.subject,
                "body": {
                    "contentType": params.content_type,
                    "content": params.body,
                },
                "toRecipients": to_recipients,
            },
            "saveToSentItems": params.save_to_sent_items,
        }

        if cc_recipients:
            request_body["message"]["ccRecipients"] = cc_recipients
        if bcc_recipients:
            request_body["message"]["bccRecipients"] = bcc_recipients

        response = await self._client.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=request_body,
        )

        # Microsoft Graph returns 202 Accepted with no body on success
        if not response.is_success:
            raise ProviderAPIError(
                "microsoft",
                response.status_code,
                "Failed to send email",
                response.text,
            )

    async def get_user_info(self, user_id: str) -> MicrosoftUserInfo:
        """
        Get user info from Microsoft Graph.

        Requires the User.Read scope.

        Args:
            user_id: User ID

        Returns:
            Microsoft user info
        """
        access_token = await self.get_valid_token(user_id)

        response = await self._client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if not response.is_success:
            raise ProviderAPIError(
                "microsoft",
                response.status_code,
                "Failed to get user info",
                response.text,
            )

        data: dict[str, Any] = response.json()
        return MicrosoftUserInfo(
            id=data["id"],
            display_name=data["displayName"],
            user_principal_name=data["userPrincipalName"],
            mail=data.get("mail"),
            given_name=data.get("givenName"),
            surname=data.get("surname"),
        )

    @staticmethod
    def _format_recipients(
        recipients: Union[str, list[str]],
    ) -> list[dict[str, dict[str, str]]]:
        """Format email recipients for Microsoft Graph API."""
        if isinstance(recipients, str):
            # Split by comma or semicolon
            email_list = [
                email.strip() for email in recipients.replace(";", ",").split(",") if email.strip()
            ]
        else:
            email_list = recipients

        return [{"emailAddress": {"address": email}} for email in email_list]
