"""
basyx-client: High-level HTTP client for the AAS Part 2 API v3.x

This package provides a BaSyx-model-native HTTP client that:
- Automatically handles base64url encoding for identifiers
- Automatically URL-encodes idShortPath (including brackets)
- Returns basyx.aas.model.* objects, not dicts
- Supports both sync and async operations via httpx
- Provides full authentication suite (Bearer, Basic, OAuth2, certificates)
"""

from basyx_client.client import AASClient
from basyx_client.exceptions import (
    AASClientError,
    BadRequestError,
    ConflictError,
    ConnectionError,
    ForbiddenError,
    ResourceNotFoundError,
    ServerError,
    TimeoutError,
    UnauthorizedError,
)
from basyx_client.pagination import PaginatedResult

__version__ = "0.1.4"

__all__ = [
    "AASClient",
    "AASClientError",
    "BadRequestError",
    "ConflictError",
    "ConnectionError",
    "ForbiddenError",
    "PaginatedResult",
    "ResourceNotFoundError",
    "ServerError",
    "TimeoutError",
    "UnauthorizedError",
]
