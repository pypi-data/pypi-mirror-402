"""LinkedIn OAuth provider with API support."""

from dataclasses import dataclass
from typing import Any, Optional

from nospoon_integrations.core.errors import ProviderAPIError
from nospoon_integrations.core.types import (
    ProviderConfig,
    ProviderEndpoints,
    TokenStorage,
)
from nospoon_integrations.providers.base_provider import BaseProvider

LINKEDIN_ENDPOINTS = ProviderEndpoints(
    auth_url="https://www.linkedin.com/oauth/v2/authorization",
    token_url="https://www.linkedin.com/oauth/v2/accessToken",
    user_info_url="https://api.linkedin.com/v2/userinfo",
)

LINKEDIN_API_URL = "https://api.linkedin.com/v2"


@dataclass
class LinkedInUserInfo:
    """LinkedIn user info (OpenID Connect)."""

    sub: str
    name: str
    given_name: str
    family_name: str
    picture: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None


@dataclass
class LinkedInOrganization:
    """LinkedIn organization info."""

    id: str
    name: str
    vanity_name: str


class LinkedInProvider(BaseProvider):
    """LinkedIn OAuth provider with API support."""

    def __init__(self, config: ProviderConfig, storage: TokenStorage) -> None:
        default_scopes = config.scopes or ["openid", "profile", "email"]
        config_with_scopes = ProviderConfig(
            client_id=config.client_id,
            client_secret=config.client_secret,
            scopes=default_scopes,
            redirect_uri=config.redirect_uri,
        )
        super().__init__("linkedin", LINKEDIN_ENDPOINTS, config_with_scopes, storage)

    # LinkedIn-specific API methods

    async def get_user_info(self, user_id: str) -> LinkedInUserInfo:
        """
        Get user info from LinkedIn using OpenID Connect.

        Args:
            user_id: User ID

        Returns:
            LinkedIn user info
        """
        access_token = await self.get_valid_token(user_id)

        response = await self._client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if not response.is_success:
            raise ProviderAPIError(
                "linkedin",
                response.status_code,
                "Failed to get user info",
                response.text,
            )

        data: dict[str, Any] = response.json()
        return LinkedInUserInfo(
            sub=data["sub"],
            name=data["name"],
            given_name=data["given_name"],
            family_name=data["family_name"],
            picture=data.get("picture"),
            email=data.get("email"),
            email_verified=data.get("email_verified"),
        )

    async def get_member_urn(self, user_id: str) -> str:
        """
        Get LinkedIn member URN (needed for posting).

        Args:
            user_id: User ID

        Returns:
            Member URN
        """
        user_info = await self.get_user_info(user_id)
        return f"urn:li:person:{user_info.sub}"

    async def share_post(
        self,
        user_id: str,
        text: str,
        visibility: str = "PUBLIC",
        article_url: Optional[str] = None,
        article_title: Optional[str] = None,
        article_description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Share a post on LinkedIn (requires w_member_social scope).

        Args:
            user_id: User ID
            text: Post text
            visibility: 'PUBLIC' or 'CONNECTIONS'
            article_url: Optional article URL
            article_title: Optional article title
            article_description: Optional article description

        Returns:
            Post result with ID
        """
        access_token = await self.get_valid_token(user_id)
        author_urn = await self.get_member_urn(user_id)

        share_content: dict[str, Any] = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "ARTICLE" if article_url else "NONE",
        }

        if article_url:
            media_item: dict[str, Any] = {
                "status": "READY",
                "originalUrl": article_url,
            }
            if article_title:
                media_item["title"] = {"text": article_title}
            if article_description:
                media_item["description"] = {"text": article_description}
            share_content["media"] = [media_item]

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

        response = await self._client.post(
            f"{LINKEDIN_API_URL}/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=payload,
        )

        if not response.is_success:
            raise ProviderAPIError(
                "linkedin",
                response.status_code,
                "Failed to share post",
                response.text,
            )

        result: dict[str, Any] = response.json()
        return result

    async def get_organizations(self, user_id: str) -> list[LinkedInOrganization]:
        """
        Get company pages the user can post to (requires w_organization_social scope).

        Args:
            user_id: User ID

        Returns:
            Array of organizations
        """
        access_token = await self.get_valid_token(user_id)

        response = await self._client.get(
            f"{LINKEDIN_API_URL}/organizationAcls?q=roleAssignee&role=ADMINISTRATOR"
            "&projection=(elements*(organization~(id,localizedName,vanityName)))",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if not response.is_success:
            raise ProviderAPIError(
                "linkedin",
                response.status_code,
                "Failed to get organizations",
                response.text,
            )

        data: dict[str, Any] = response.json()
        organizations: list[LinkedInOrganization] = []

        for element in data.get("elements", []):
            org = element.get("organization~")
            if org:
                organizations.append(
                    LinkedInOrganization(
                        id=org["id"],
                        name=org["localizedName"],
                        vanity_name=org["vanityName"],
                    )
                )

        return organizations
