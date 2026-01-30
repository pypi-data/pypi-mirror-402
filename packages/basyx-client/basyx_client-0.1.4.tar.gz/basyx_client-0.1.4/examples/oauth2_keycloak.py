#!/usr/bin/env python3
"""OAuth2 authentication with Keycloak.

This example demonstrates:
- OAuth2 client credentials flow
- Token auto-refresh
- Environment-based configuration

Prerequisites:
    pip install basyx-client[oauth]

Environment variables:
    KEYCLOAK_TOKEN_URL - Keycloak token endpoint
    KEYCLOAK_CLIENT_ID - Client ID
    KEYCLOAK_CLIENT_SECRET - Client secret
    BASYX_URL - AAS server URL (optional, defaults to localhost)
"""

import os
import sys

# Check for authlib
try:
    from basyx_client.auth import OAuth2ClientCredentials
except ImportError:
    print("Error: OAuth2 support requires authlib")
    print("Install with: pip install basyx-client[oauth]")
    sys.exit(1)

from basyx_client import AASClient


def get_config() -> dict:
    """Get configuration from environment."""
    required = ["KEYCLOAK_TOKEN_URL", "KEYCLOAK_CLIENT_ID", "KEYCLOAK_CLIENT_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]

    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nExample usage:")
        print("  export KEYCLOAK_TOKEN_URL=https://keycloak.example.com/realms/aas/protocol/openid-connect/token")
        print("  export KEYCLOAK_CLIENT_ID=basyx-client")
        print("  export KEYCLOAK_CLIENT_SECRET=your-secret")
        print("  python oauth2_keycloak.py")
        sys.exit(1)

    return {
        "token_url": os.environ["KEYCLOAK_TOKEN_URL"],
        "client_id": os.environ["KEYCLOAK_CLIENT_ID"],
        "client_secret": os.environ["KEYCLOAK_CLIENT_SECRET"],
        "base_url": os.environ.get("BASYX_URL", "http://localhost:8081"),
        "scope": os.environ.get("KEYCLOAK_SCOPE", "openid"),
    }


def main() -> None:
    """Run OAuth2 example."""
    print("=== basyx-client OAuth2 Example ===\n")

    config = get_config()
    print(f"Token URL: {config['token_url']}")
    print(f"Client ID: {config['client_id']}")
    print(f"Base URL: {config['base_url']}")
    print()

    # Create OAuth2 auth
    auth = OAuth2ClientCredentials(
        token_url=config["token_url"],
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        scope=config["scope"],
        token_refresh_buffer=60,  # Refresh 60s before expiry
    )

    print("Authenticating...")

    with AASClient(config["base_url"], auth=auth) as client:
        print("Authentication successful!\n")

        # List shells
        result = client.shells.list(limit=10)
        print(f"Found {len(result.result)} AAS shells:")

        for shell in result.result:
            print(f"  - {shell.id_short}: {shell.id}")

        if not result.result:
            print("  (no shells found)")

        # List submodels
        print()
        result = client.submodels.list(limit=10)
        print(f"Found {len(result.result)} submodels:")

        for sm in result.result:
            print(f"  - {sm.id_short}: {sm.id}")

        if not result.result:
            print("  (no submodels found)")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
