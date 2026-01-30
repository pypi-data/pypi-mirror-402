"""Unit tests for authentication providers."""

import httpx

from basyx_client.auth import BearerAuth, CertificateConfig, OAuth2ClientCredentials


class TestBearerAuth:
    """Tests for BearerAuth class."""

    def test_adds_authorization_header(self) -> None:
        """Test that BearerAuth adds Authorization header."""
        auth = BearerAuth("my-token-123")

        # Create a mock request
        request = httpx.Request("GET", "http://example.com/api")

        # Apply auth
        flow = auth.auth_flow(request)
        modified_request = next(flow)

        assert "Authorization" in modified_request.headers
        assert modified_request.headers["Authorization"] == "Bearer my-token-123"

    def test_token_stored(self) -> None:
        """Test that token is stored."""
        auth = BearerAuth("secret-token")
        assert auth.token == "secret-token"


class TestOAuth2ClientCredentials:
    """Tests for OAuth2ClientCredentials class."""

    def test_initialization(self) -> None:
        """Test OAuth2 auth initialization."""
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/oauth/token",
            client_id="my-client",
            client_secret="my-secret",
            scope="read write",
        )

        assert auth.token_url == "https://auth.example.com/oauth/token"
        assert auth.client_id == "my-client"
        assert auth.client_secret == "my-secret"
        assert auth.scope == "read write"
        assert auth._token is None

    def test_needs_refresh_when_no_token(self) -> None:
        """Test that refresh is needed when no token exists."""
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/token",
            client_id="client",
            client_secret="secret",
        )

        assert auth._needs_refresh() is True

    def test_needs_refresh_when_token_exists(self) -> None:
        """Test that refresh is not needed when valid token exists."""
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/token",
            client_id="client",
            client_secret="secret",
        )

        # Manually set token (simulating successful auth)
        auth._token = "valid-token"
        auth._expires_at = None  # No expiry

        assert auth._needs_refresh() is False

    def test_build_token_request(self) -> None:
        """Test building the token request."""
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/token",
            client_id="my-client",
            client_secret="my-secret",
            scope="aas:read",
        )

        request = auth._build_token_request()

        assert request.method == "POST"
        assert str(request.url) == "https://auth.example.com/token"
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"

    def test_handle_token_response(self) -> None:
        """Test handling token response."""
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/token",
            client_id="client",
            client_secret="secret",
        )

        # Create mock response
        class MockResponse:
            def json(self):
                return {
                    "access_token": "new-access-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }

        auth._handle_token_response(MockResponse())

        assert auth._token == "new-access-token"
        assert auth._expires_at is not None


class TestCertificateConfig:
    """Tests for CertificateConfig class."""

    def test_cert_only(self) -> None:
        """Test certificate config with single file."""
        config = CertificateConfig("/path/to/combined.pem")

        assert config.cert_path == "/path/to/combined.pem"
        assert config.key_path is None
        assert config.cert == "/path/to/combined.pem"

    def test_cert_and_key(self) -> None:
        """Test certificate config with separate files."""
        config = CertificateConfig("/path/to/cert.pem", "/path/to/key.pem")

        assert config.cert_path == "/path/to/cert.pem"
        assert config.key_path == "/path/to/key.pem"
        assert config.cert == ("/path/to/cert.pem", "/path/to/key.pem")
