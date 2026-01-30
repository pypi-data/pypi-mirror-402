"""
Main AAS client with namespaced endpoint access.

This is the primary entry point for the library. The client manages
HTTP connections and provides access to all API endpoints through
namespaced attributes.

Example:
    # Sync usage
    with AASClient("http://localhost:8081/api/v3.0") as client:
        aas = client.shells.get("urn:example:aas:123")
        print(aas.id_short)

    # Async usage
    async with AASClient("http://localhost:8081/api/v3.0") as client:
        aas = await client.shells.get_async("urn:example:aas:123")
        print(aas.id_short)
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from basyx_client.auth import BearerAuth, CertificateConfig, OAuth2ClientCredentials


class AASClient:
    """
    High-level HTTP client for the AAS Part 2 API v3.x.

    Key features:
    - Automatic base64url encoding for identifiers
    - Automatic URL encoding for idShortPath
    - Returns basyx.aas.model.* objects, not dicts
    - Supports both sync and async operations
    - Full auth suite (Bearer, Basic, OAuth2, certificates)

    Attributes:
        shells: AAS Repository endpoint (CRUD for AssetAdministrationShell)
        submodels: Submodel Repository endpoint (CRUD for Submodels)
        concept_descriptions: Concept Description endpoint
        aas_registry: AAS Registry endpoint
        submodel_registry: Submodel Registry endpoint
        packages: AASX Server endpoint
        discovery: Discovery endpoint

    Example:
        # Basic usage
        client = AASClient("http://localhost:8081/api/v3.0")

        # With Bearer token
        from basyx_client.auth import BearerAuth
        client = AASClient("http://localhost:8081/api/v3.0", auth=BearerAuth("my-token"))

        # With Basic auth (tuple shorthand)
        client = AASClient("http://localhost:8081/api/v3.0", auth=("user", "pass"))

        # With OAuth2 client credentials
        from basyx_client.auth import OAuth2ClientCredentials
        client = AASClient("http://localhost:8081/api/v3.0", auth=OAuth2ClientCredentials(
            token_url="https://auth.example.com/token",
            client_id="my-client",
            client_secret="my-secret",
        ))

        # With mTLS
        client = AASClient(
            "https://secure.example.com/api/v3.0",
            cert=("/path/to/cert.pem", "/path/to/key.pem"),
        )
    """

    def __init__(
        self,
        base_url: str,
        *,
        auth: httpx.Auth
        | BearerAuth
        | OAuth2ClientCredentials
        | tuple[str, str]
        | str
        | None = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        cert: str | tuple[str, str] | CertificateConfig | None = None,
        encode_package_id: bool = True,
        encode_discovery_asset_ids: bool = True,
    ) -> None:
        """
        Initialize the AAS client.

        Args:
            base_url: Base URL of the AAS API (e.g., "http://localhost:8081/api/v3.0")
            auth: Authentication provider. Can be:
                  - httpx.Auth subclass (BearerAuth, OAuth2ClientCredentials)
                  - tuple of (username, password) for Basic auth
                  - string for Bearer token (shorthand)
                  - None for no auth
            timeout: Request timeout in seconds (default 30)
            verify_ssl: Whether to verify SSL certificates (default True)
            cert: Client certificate for mTLS. Can be:
                  - Path to combined cert/key file
                  - Tuple of (cert_path, key_path)
                  - CertificateConfig instance
            encode_package_id: Base64url encode AASX package IDs in paths (default True)
            encode_discovery_asset_ids: Base64url encode Discovery assetIds query params (default True)
        """
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._auth = self._resolve_auth(auth)
        self._cert = self._resolve_cert(cert)
        self._encode_package_id = encode_package_id
        self._encode_discovery_asset_ids = encode_discovery_asset_ids

        # HTTP clients (lazy initialization) - stored in __dict__ to avoid property recursion
        self.__dict__["_sync_client"] = None
        self.__dict__["_async_client"] = None

        # Initialize endpoint namespaces
        self._init_endpoints()

    def _init_endpoints(self) -> None:
        """Initialize all endpoint namespaces."""
        from basyx_client.endpoints.aas_registry import AASRegistryEndpoint
        from basyx_client.endpoints.aas_repository import AASRepositoryEndpoint
        from basyx_client.endpoints.aasx_server import AASXServerEndpoint
        from basyx_client.endpoints.concept_descriptions import ConceptDescriptionEndpoint
        from basyx_client.endpoints.discovery import DiscoveryEndpoint
        from basyx_client.endpoints.submodel_registry import SubmodelRegistryEndpoint
        from basyx_client.endpoints.submodel_repository import SubmodelRepositoryEndpoint

        self.shells = AASRepositoryEndpoint(self)
        self.submodels = SubmodelRepositoryEndpoint(self)
        self.concept_descriptions = ConceptDescriptionEndpoint(self)
        self.aas_registry = AASRegistryEndpoint(self)
        self.submodel_registry = SubmodelRegistryEndpoint(self)
        self.packages = AASXServerEndpoint(self)
        self.discovery = DiscoveryEndpoint(self)

    def _resolve_auth(
        self,
        auth: httpx.Auth | tuple[str, str] | str | None,
    ) -> httpx.Auth | None:
        """Resolve auth parameter to httpx.Auth instance."""
        if auth is None:
            return None
        if isinstance(auth, httpx.Auth):
            return auth
        if isinstance(auth, tuple) and len(auth) == 2:
            return httpx.BasicAuth(auth[0], auth[1])
        if isinstance(auth, str):
            from basyx_client.auth import BearerAuth

            return BearerAuth(auth)
        raise ValueError(f"Unsupported auth type: {type(auth)}")

    def _resolve_cert(
        self,
        cert: str | tuple[str, str] | CertificateConfig | None,
    ) -> str | tuple[str, str] | None:
        """Resolve cert parameter to httpx-compatible format."""
        if cert is None:
            return None
        if isinstance(cert, (str, tuple)):
            return cert

        # Handle CertificateConfig
        from basyx_client.auth import CertificateConfig

        if isinstance(cert, CertificateConfig):
            return cert.cert

        raise ValueError(f"Unsupported cert type: {type(cert)}")

    def _get_sync_client(self) -> httpx.Client:
        """Get or create the synchronous HTTP client."""
        if self.__dict__["_sync_client"] is None:
            self.__dict__["_sync_client"] = httpx.Client(
                auth=self._auth,
                timeout=self._timeout,
                verify=self._verify_ssl,
                cert=self._cert,
            )
        return self.__dict__["_sync_client"]

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create the asynchronous HTTP client."""
        if self.__dict__["_async_client"] is None:
            self.__dict__["_async_client"] = httpx.AsyncClient(
                auth=self._auth,
                timeout=self._timeout,
                verify=self._verify_ssl,
                cert=self._cert,
            )
        return self.__dict__["_async_client"]

    @property
    def _sync_client(self) -> httpx.Client:
        """Property wrapper that ensures sync client exists."""
        return self._get_sync_client()

    @_sync_client.setter
    def _sync_client(self, value: httpx.Client | None) -> None:
        """Setter for sync client."""
        self.__dict__["_sync_client"] = value

    @property
    def _async_client(self) -> httpx.AsyncClient:
        """Property wrapper that ensures async client exists."""
        return self._get_async_client()

    @_async_client.setter
    def _async_client(self, value: httpx.AsyncClient | None) -> None:
        """Setter for async client."""
        self.__dict__["_async_client"] = value

    # Context manager support (sync)
    def __enter__(self) -> AASClient:
        """Enter sync context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit sync context manager - close sync client."""
        self.close()

    # Context manager support (async)
    async def __aenter__(self) -> AASClient:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager - close async client."""
        await self.aclose()

    def close(self) -> None:
        """Close the synchronous HTTP client."""
        if self.__dict__.get("_sync_client") is not None:
            self.__dict__["_sync_client"].close()
            self.__dict__["_sync_client"] = None

    async def aclose(self) -> None:
        """Close the asynchronous HTTP client."""
        if self.__dict__.get("_async_client") is not None:
            await self.__dict__["_async_client"].aclose()
            self.__dict__["_async_client"] = None
