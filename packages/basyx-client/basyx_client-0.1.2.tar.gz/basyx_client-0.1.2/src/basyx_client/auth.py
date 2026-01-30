"""
Authentication providers for AAS Part 2 API client.

Supports multiple authentication methods:
- Bearer token (static)
- Basic authentication (username/password)
- OAuth2 client credentials flow (with automatic token refresh)
- mTLS client certificates

Example:
    # Bearer token
    client = AASClient("http://localhost:8081", auth=BearerAuth("my-token"))

    # Basic auth
    client = AASClient("http://localhost:8081", auth=("user", "pass"))

    # OAuth2
    client = AASClient("http://localhost:8081", auth=OAuth2ClientCredentials(
        token_url="https://auth.example.com/token",
        client_id="my-client",
        client_secret="my-secret",
    ))

    # mTLS
    client = AASClient("http://localhost:8081", cert=("/path/to/cert.pem", "/path/to/key.pem"))
"""

from __future__ import annotations

import time
from collections.abc import Generator
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from httpx import Request, Response


class BearerAuth(httpx.Auth):
    """
    Bearer token authentication.

    Adds an Authorization header with the Bearer scheme to all requests.

    Args:
        token: The bearer token to use for authentication
    """

    def __init__(self, token: str) -> None:
        self.token = token

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


class OAuth2ClientCredentials(httpx.Auth):
    """
    OAuth2 client credentials flow with automatic token refresh.

    Obtains an access token using client credentials and automatically
    refreshes it when expired.

    Args:
        token_url: The OAuth2 token endpoint URL
        client_id: The client ID
        client_secret: The client secret
        scope: Optional scope(s) to request (space-separated if multiple)

    Example:
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/oauth/token",
            client_id="my-client-id",
            client_secret="my-client-secret",
            scope="aas:read aas:write",
        )
        client = AASClient("http://localhost:8081", auth=auth)
    """

    requires_response_body = True

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
    ) -> None:
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self._token: str | None = None
        self._expires_at: float | None = None

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        if self._needs_refresh():
            # Request a new token
            token_request = self._build_token_request()
            token_response = yield token_request

            if token_response.status_code == 200:
                self._handle_token_response(token_response)

        if self._token:
            request.headers["Authorization"] = f"Bearer {self._token}"
        yield request

    def _needs_refresh(self) -> bool:
        """Check if token needs to be refreshed."""
        if self._token is None:
            return True
        if self._expires_at is None:
            return False
        # Refresh 60 seconds before expiry
        return time.time() > (self._expires_at - 60)

    def _build_token_request(self) -> Request:
        """Build the token request."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            data["scope"] = self.scope

        return httpx.Request(
            "POST",
            self.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def _handle_token_response(self, response: Response) -> None:
        """Parse and store the token from the response."""
        data = response.json()
        self._token = data["access_token"]
        expires_in = data.get("expires_in")
        if expires_in:
            self._expires_at = time.time() + int(expires_in)
        else:
            self._expires_at = None


class CertificateConfig:
    """
    Configuration for mTLS client certificate authentication.

    This is not an httpx.Auth subclass - it's a configuration holder.
    The cert tuple is passed directly to the httpx client.

    Args:
        cert_path: Path to the client certificate file (PEM format)
        key_path: Path to the private key file (PEM format). If None, the key
                  is expected to be in the same file as the certificate.

    Example:
        # Separate cert and key files
        cert_config = CertificateConfig("/path/to/cert.pem", "/path/to/key.pem")

        # Combined cert and key in one file
        cert_config = CertificateConfig("/path/to/combined.pem")
    """

    def __init__(self, cert_path: str, key_path: str | None = None) -> None:
        self.cert_path = cert_path
        self.key_path = key_path

    @property
    def cert(self) -> str | tuple[str, str]:
        """Return the cert configuration for httpx."""
        if self.key_path:
            return (self.cert_path, self.key_path)
        return self.cert_path
