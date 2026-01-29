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

__all__ = [
    "BaseProvider",
    "DraftEmailParams",
    "FacebookProvider",
    "GoogleProvider",
    "HubSpotContact",
    "HubSpotProvider",
    "LinkedInProvider",
    "SecureCallbackFailure",
    "SecureCallbackResult",
    "SecureCallbackSuccess",
]
