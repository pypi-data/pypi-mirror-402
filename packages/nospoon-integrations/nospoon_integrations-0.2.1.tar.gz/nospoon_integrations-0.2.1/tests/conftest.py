"""Pytest configuration and fixtures."""

import pytest

from nospoon_integrations.core.types import ProviderConfig
from nospoon_integrations.storage.memory import MemoryTokenStorage


@pytest.fixture
def memory_storage() -> MemoryTokenStorage:
    """Create a fresh in-memory token storage for testing."""
    return MemoryTokenStorage()


@pytest.fixture
def google_config() -> ProviderConfig:
    """Create a test Google provider config."""
    return ProviderConfig(
        client_id="test-client-id",
        client_secret="test-client-secret",
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )


@pytest.fixture
def hubspot_config() -> ProviderConfig:
    """Create a test HubSpot provider config."""
    return ProviderConfig(
        client_id="test-hubspot-client-id",
        client_secret="test-hubspot-client-secret",
        scopes=["crm.objects.contacts.read", "crm.objects.contacts.write"],
    )
