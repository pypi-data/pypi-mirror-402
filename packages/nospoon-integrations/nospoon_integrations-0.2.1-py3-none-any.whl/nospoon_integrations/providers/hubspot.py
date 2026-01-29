"""HubSpot OAuth provider with CRM API support."""

from dataclasses import dataclass
from typing import Any, Optional

from nospoon_integrations.core.errors import ProviderAPIError
from nospoon_integrations.core.types import (
    ProviderConfig,
    ProviderEndpoints,
    TokenRefreshResult,
    TokenStorage,
)
from nospoon_integrations.providers.base_provider import BaseProvider

HUBSPOT_ENDPOINTS = ProviderEndpoints(
    auth_url="https://app.hubspot.com/oauth/authorize",
    token_url="https://api.hubapi.com/oauth/v1/token",
)

HUBSPOT_API_URL = "https://api.hubapi.com"


@dataclass
class HubSpotContact:
    """HubSpot contact data."""

    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    mobile: Optional[str] = None
    office_phone: Optional[str] = None
    company_website: Optional[str] = None
    office_location: Optional[str] = None
    industry: Optional[str] = None
    linkedin_company_url: Optional[str] = None
    about_company: Optional[str] = None
    where_we_met: Optional[str] = None


@dataclass
class HubSpotContactResult:
    """HubSpot contact result."""

    id: str
    properties: dict[str, str]
    created_at: str
    updated_at: str


class HubSpotProvider(BaseProvider):
    """HubSpot OAuth provider with CRM API support."""

    def __init__(self, config: ProviderConfig, storage: TokenStorage) -> None:
        default_scopes = config.scopes or [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write",
        ]
        config_with_scopes = ProviderConfig(
            client_id=config.client_id,
            client_secret=config.client_secret,
            scopes=default_scopes,
            redirect_uri=config.redirect_uri,
        )
        super().__init__("hubspot", HUBSPOT_ENDPOINTS, config_with_scopes, storage)

    def _parse_refresh_token_response(self, data: dict[str, Any]) -> TokenRefreshResult:
        """HubSpot returns new refresh token on each refresh."""
        return TokenRefreshResult(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),  # HubSpot always returns new one
            expires_in=data.get("expires_in", 21600),  # 6 hours default
            scope=data.get("scope"),
        )

    # HubSpot-specific API methods

    async def create_contact(
        self, user_id: str, contact: HubSpotContact
    ) -> tuple[HubSpotContactResult, bool]:
        """
        Create or update a contact in HubSpot.

        Args:
            user_id: User ID
            contact: Contact data

        Returns:
            Tuple of (contact result, was_updated)
        """
        access_token = await self.get_valid_token(user_id)
        properties = self._map_contact_to_properties(contact)

        # Check if contact exists by email
        existing_contact_id: Optional[str] = None
        if contact.contact_email:
            existing_contact_id = await self._find_contact_by_email(
                access_token, contact.contact_email
            )

        if existing_contact_id:
            # Update existing contact
            response = await self._client.patch(
                f"{HUBSPOT_API_URL}/crm/v3/objects/contacts/{existing_contact_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"properties": properties},
            )
        else:
            # Create new contact
            response = await self._client.post(
                f"{HUBSPOT_API_URL}/crm/v3/objects/contacts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"properties": properties},
            )

        if not response.is_success:
            raise ProviderAPIError(
                "hubspot",
                response.status_code,
                "Failed to create/update contact",
                response.text,
            )

        data: dict[str, Any] = response.json()
        result = HubSpotContactResult(
            id=data["id"],
            properties=data.get("properties", {}),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
        )
        return result, existing_contact_id is not None

    async def batch_create_contacts(
        self, user_id: str, contacts: list[HubSpotContact]
    ) -> tuple[list[HubSpotContactResult], list[Any]]:
        """
        Batch create contacts in HubSpot.

        Args:
            user_id: User ID
            contacts: Array of contacts

        Returns:
            Tuple of (results, errors)
        """
        access_token = await self.get_valid_token(user_id)

        inputs = [{"properties": self._map_contact_to_properties(contact)} for contact in contacts]

        response = await self._client.post(
            f"{HUBSPOT_API_URL}/crm/v3/objects/contacts/batch/create",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"inputs": inputs},
        )

        if not response.is_success:
            raise ProviderAPIError(
                "hubspot",
                response.status_code,
                "Failed to batch create contacts",
                response.text,
            )

        data: dict[str, Any] = response.json()
        results = [
            HubSpotContactResult(
                id=r["id"],
                properties=r.get("properties", {}),
                created_at=r.get("createdAt", ""),
                updated_at=r.get("updatedAt", ""),
            )
            for r in data.get("results", [])
        ]
        return results, data.get("errors", [])

    async def _find_contact_by_email(self, access_token: str, email: str) -> Optional[str]:
        """Search for a contact by email."""
        response = await self._client.post(
            f"{HUBSPOT_API_URL}/crm/v3/objects/contacts/search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email,
                            }
                        ]
                    }
                ]
            },
        )

        if not response.is_success:
            return None

        data: dict[str, Any] = response.json()
        results = data.get("results", [])
        return results[0]["id"] if results else None

    def _map_contact_to_properties(self, contact: HubSpotContact) -> dict[str, str]:
        """Map contact data to HubSpot properties."""
        properties: dict[str, str] = {}

        if contact.contact_person:
            first_name, last_name = self._split_name(contact.contact_person)
            if first_name:
                properties["firstname"] = first_name
            if last_name:
                properties["lastname"] = last_name

        if contact.contact_email:
            properties["email"] = contact.contact_email
        if contact.company_name:
            properties["company"] = contact.company_name
        if contact.job_title:
            properties["jobtitle"] = contact.job_title
        if contact.mobile:
            properties["mobilephone"] = contact.mobile
        if contact.office_phone:
            properties["phone"] = contact.office_phone
        if contact.company_website:
            properties["website"] = contact.company_website
        if contact.office_location:
            properties["address"] = contact.office_location
        if contact.industry:
            properties["industry"] = contact.industry

        # Build notes from additional fields
        notes: list[str] = []
        if contact.linkedin_company_url:
            notes.append(f"LinkedIn: {contact.linkedin_company_url}")
        if contact.about_company:
            notes.append(f"About: {contact.about_company}")
        if contact.where_we_met:
            notes.append(f"Met at: {contact.where_we_met}")

        if notes:
            properties["hs_content_membership_notes"] = "\n\n".join(notes)

        return properties

    @staticmethod
    def _split_name(full_name: str) -> tuple[str, str]:
        """Split full name into first and last name."""
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], " ".join(parts[1:])
