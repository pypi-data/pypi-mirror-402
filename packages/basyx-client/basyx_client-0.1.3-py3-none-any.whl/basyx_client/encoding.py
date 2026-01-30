"""
Encoding utilities for AAS Part 2 API v3.x.

The API requires:
- Identifiers to be base64url encoded (RFC 4648 §5) without padding
- idShortPath segments to be URL-encoded (brackets become %5B %5D)

These are the #1 source of pain when working with the API manually.
"""

import base64
import urllib.parse


def encode_identifier(identifier: str) -> str:
    """
    Base64url encode an identifier for use in API paths.

    The AAS Part 2 API requires identifiers to be encoded using base64url
    (RFC 4648 §5) without trailing padding characters.

    Args:
        identifier: The identifier to encode (e.g., "https://acme.org/ids/aas/55")

    Returns:
        Base64url encoded string without padding (e.g., "aHR0cHM6Ly9hY21lLm9yZy9pZHMvYWFzLzU1")

    Example:
        >>> encode_identifier("https://acme.org/ids/aas/55")
        'aHR0cHM6Ly9hY21lLm9yZy9pZHMvYWFzLzU1'
    """
    encoded = base64.urlsafe_b64encode(identifier.encode("utf-8"))
    return encoded.rstrip(b"=").decode("ascii")


def decode_identifier(encoded: str) -> str:
    """
    Decode a base64url encoded identifier.

    Restores the padding characters that were stripped during encoding
    before decoding.

    Args:
        encoded: Base64url encoded identifier without padding

    Returns:
        Original identifier string

    Example:
        >>> decode_identifier("aHR0cHM6Ly9hY21lLm9yZy9pZHMvYWFzLzU1")
        'https://acme.org/ids/aas/55'
    """
    # Restore padding - base64 requires length to be multiple of 4
    padding_needed = 4 - (len(encoded) % 4)
    if padding_needed != 4:
        encoded += "=" * padding_needed
    return base64.urlsafe_b64decode(encoded).decode("utf-8")


def encode_id_short_path(path: str) -> str:
    """
    URL-encode an idShortPath for use in API paths.

    The idShortPath uses dots for hierarchy and brackets for array indices:
    - "Sensors.Measurements[0].Temperature"

    The brackets must be URL-encoded as %5B and %5D. Dots, hyphens,
    underscores, and tildes are preserved as they're safe characters.

    Args:
        path: The idShortPath (e.g., "Sensors.Measurements[0].Temperature")

    Returns:
        URL-encoded path (e.g., "Sensors.Measurements%5B0%5D.Temperature")

    Example:
        >>> encode_id_short_path("Sensors.Measurements[0].Temperature")
        'Sensors.Measurements%5B0%5D.Temperature'
    """
    # safe characters: dots for hierarchy, hyphens/underscores/tilde per RFC 3986
    return urllib.parse.quote(path, safe=".-_~")


def decode_id_short_path(encoded_path: str) -> str:
    """
    Decode a URL-encoded idShortPath.

    Args:
        encoded_path: URL-encoded idShortPath

    Returns:
        Original idShortPath string

    Example:
        >>> decode_id_short_path("Sensors.Measurements%5B0%5D.Temperature")
        'Sensors.Measurements[0].Temperature'
    """
    return urllib.parse.unquote(encoded_path)
