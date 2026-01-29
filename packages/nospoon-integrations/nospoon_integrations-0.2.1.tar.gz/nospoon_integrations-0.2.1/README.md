# NoSpoon Integrations - Python SDK

Cross-platform OAuth integrations SDK for NoSpoon applications.

## Installation

```bash
pip install nospoon-integrations

# With Supabase support
pip install nospoon-integrations[supabase]
```

## Quick Start

```python
import os
from nospoon_integrations import IntegrationClient, IntegrationClientConfig, ProviderConfig
from nospoon_integrations.storage import SupabaseTokenStorage

# Initialize storage
storage = SupabaseTokenStorage(
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
)

# Initialize client with providers
integrations = IntegrationClient(IntegrationClientConfig(
    storage=storage,
    google=ProviderConfig(
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    ),
    hubspot=ProviderConfig(
        client_id=os.environ["HUBSPOT_CLIENT_ID"],
        client_secret=os.environ["HUBSPOT_CLIENT_SECRET"],
    ),
))

# Use providers
auth_url = integrations.google.get_auth_url("https://myapp.com/callback")
status = await integrations.google.get_connection_status(user_id)
```

## Providers

- **Google** - Gmail API, OAuth
- **HubSpot** - CRM contacts, OAuth
- **Facebook** - Graph API, Pages
- **LinkedIn** - Posts, OAuth

## Documentation

See the [main documentation](https://github.com/nospoon/integrations) for full usage details.

## License

MIT
