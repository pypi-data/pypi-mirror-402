"""OAuth providers for the integrations SDK."""

from nospoon_integrations.providers.base_provider import (
    BaseProvider,
    SecureCallbackFailure,
    SecureCallbackResult,
    SecureCallbackSuccess,
)
from nospoon_integrations.providers.facebook import FacebookProvider
from nospoon_integrations.providers.google import DraftEmailParams, GoogleProvider
from nospoon_integrations.providers.hubspot import HubSpotContact, HubSpotProvider
from nospoon_integrations.providers.linkedin import LinkedInProvider
from nospoon_integrations.providers.microsoft import (
    MICROSOFT_EMAIL_SCOPE,
    MICROSOFT_MAIL_READ_SCOPE,
    MICROSOFT_MAIL_READWRITE_SCOPE,
    MICROSOFT_MAIL_SEND_SCOPE,
    MICROSOFT_OFFLINE_ACCESS_SCOPE,
    MICROSOFT_OPENID_SCOPE,
    MICROSOFT_PROFILE_SCOPE,
    MICROSOFT_USER_READ_SCOPE,
    MicrosoftProvider,
    MicrosoftSendEmailParams,
    MicrosoftUserInfo,
)

__all__ = [
    "MICROSOFT_EMAIL_SCOPE",
    "MICROSOFT_MAIL_READWRITE_SCOPE",
    "MICROSOFT_MAIL_READ_SCOPE",
    "MICROSOFT_MAIL_SEND_SCOPE",
    "MICROSOFT_OFFLINE_ACCESS_SCOPE",
    "MICROSOFT_OPENID_SCOPE",
    "MICROSOFT_PROFILE_SCOPE",
    "MICROSOFT_USER_READ_SCOPE",
    "BaseProvider",
    "DraftEmailParams",
    "FacebookProvider",
    "GoogleProvider",
    "HubSpotContact",
    "HubSpotProvider",
    "LinkedInProvider",
    "MicrosoftProvider",
    "MicrosoftSendEmailParams",
    "MicrosoftUserInfo",
    "SecureCallbackFailure",
    "SecureCallbackResult",
    "SecureCallbackSuccess",
]
