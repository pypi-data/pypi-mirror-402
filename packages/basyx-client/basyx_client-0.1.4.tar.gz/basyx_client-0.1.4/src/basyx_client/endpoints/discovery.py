"""
Discovery endpoint implementation.

Provides operations for Asset-to-AAS discovery:
- GET /lookup/shells → get_aas_ids_by_asset()
- POST /lookup/shells → link_aas_to_asset()
- DELETE /lookup/shells/{aasId} → unlink_aas()
- DELETE /lookup/shells/{aasId}/{assetId} → unlink_asset_from_aas()

The Discovery service enables looking up AAS identifiers based on
asset identifiers (e.g., serial number, manufacturer part ID).
"""

from __future__ import annotations

from typing import Any

from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.pagination import PaginatedResult


class DiscoveryEndpoint(BaseEndpoint):
    """
    Discovery endpoint for asset-to-AAS lookups.

    The Discovery service maintains a mapping between asset identifiers
    (like serial numbers) and AAS identifiers, enabling lookup of
    which AAS represents a given physical asset.

    Example:
        # Find AAS by asset serial number
        aas_ids = client.discovery.get_aas_ids_by_asset([
            {"name": "serialNumber", "value": "SN-12345"}
        ])

        # Link an AAS to an asset
        client.discovery.link_aas_to_asset(
            aas_id="urn:example:aas:123",
            asset_ids=[{"name": "serialNumber", "value": "SN-12345"}]
        )
    """

    def get_aas_ids_by_asset(
        self,
        asset_ids: list[dict[str, str]],
        limit: int = 100,
        cursor: str | None = None,
    ) -> PaginatedResult[str]:
        """
        Get AAS identifiers for given asset identifiers.

        Args:
            asset_ids: List of asset identifier dicts, each with "name" and "value" keys
                       e.g., [{"name": "serialNumber", "value": "SN-12345"}]
            limit: Maximum number of results
            cursor: Pagination cursor

        Returns:
            PaginatedResult containing AAS identifier strings

        Example:
            # Find by serial number
            result = client.discovery.get_aas_ids_by_asset([
                {"name": "serialNumber", "value": "SN-12345"}
            ])
            for aas_id in result.items:
                print(aas_id)

            # Find by multiple identifiers (AND logic)
            result = client.discovery.get_aas_ids_by_asset([
                {"name": "manufacturerId", "value": "ACME"},
                {"name": "partNumber", "value": "PN-001"}
            ])
        """
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        # Asset IDs are passed as query parameters.
        # Format: assetIds=name:value (optionally base64url encoded)
        encoded_asset_ids = []
        for aid in asset_ids:
            id_string = f"{aid['name']}:{aid['value']}"
            if self._client._encode_discovery_asset_ids:
                encoded_asset_ids.append(encode_identifier(id_string))
            else:
                encoded_asset_ids.append(id_string)
        params["assetIds"] = encoded_asset_ids

        response = self._request("GET", "/lookup/shells", params=params)
        return self._parse_string_paginated_response(response)

    async def get_aas_ids_by_asset_async(
        self,
        asset_ids: list[dict[str, str]],
        limit: int = 100,
        cursor: str | None = None,
    ) -> PaginatedResult[str]:
        """Async version of get_aas_ids_by_asset()."""
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        encoded_asset_ids = []
        for aid in asset_ids:
            id_string = f"{aid['name']}:{aid['value']}"
            if self._client._encode_discovery_asset_ids:
                encoded_asset_ids.append(encode_identifier(id_string))
            else:
                encoded_asset_ids.append(id_string)
        params["assetIds"] = encoded_asset_ids

        response = await self._request_async("GET", "/lookup/shells", params=params)
        return self._parse_string_paginated_response(response)

    def link_aas_to_asset(
        self,
        aas_id: str,
        asset_ids: list[dict[str, str]],
    ) -> None:
        """
        Link an AAS to one or more asset identifiers.

        Args:
            aas_id: The identifier of the AAS
            asset_ids: List of asset identifier dicts to link

        Raises:
            BadRequestError: If the request data is invalid
        """
        # POST body contains the AAS ID and asset links
        payload = {
            "aasId": aas_id,
            "specificAssetIds": [{"name": aid["name"], "value": aid["value"]} for aid in asset_ids],
        }
        self._request("POST", "/lookup/shells", json=payload)

    async def link_aas_to_asset_async(
        self,
        aas_id: str,
        asset_ids: list[dict[str, str]],
    ) -> None:
        """Async version of link_aas_to_asset()."""
        payload = {
            "aasId": aas_id,
            "specificAssetIds": [{"name": aid["name"], "value": aid["value"]} for aid in asset_ids],
        }
        await self._request_async("POST", "/lookup/shells", json=payload)

    def unlink_aas(self, aas_id: str) -> None:
        """
        Remove all asset links for an AAS.

        Args:
            aas_id: The identifier of the AAS to unlink

        Raises:
            ResourceNotFoundError: If no links exist for this AAS
        """
        encoded_id = encode_identifier(aas_id)
        self._request("DELETE", f"/lookup/shells/{encoded_id}")

    async def unlink_aas_async(self, aas_id: str) -> None:
        """Async version of unlink_aas()."""
        encoded_id = encode_identifier(aas_id)
        await self._request_async("DELETE", f"/lookup/shells/{encoded_id}")

    def unlink_asset_from_aas(self, aas_id: str, asset_id: dict[str, str]) -> None:
        """
        Remove a specific asset identifier link from an AAS.

        Args:
            aas_id: The identifier of the AAS
            asset_id: Asset identifier dict with "name" and "value"
        """
        encoded_aas = encode_identifier(aas_id)
        asset_string = f"{asset_id['name']}:{asset_id['value']}"
        encoded_asset = (
            encode_identifier(asset_string)
            if self._client._encode_discovery_asset_ids
            else asset_string
        )
        self._request("DELETE", f"/lookup/shells/{encoded_aas}/{encoded_asset}")

    async def unlink_asset_from_aas_async(self, aas_id: str, asset_id: dict[str, str]) -> None:
        """Async version of unlink_asset_from_aas()."""
        encoded_aas = encode_identifier(aas_id)
        asset_string = f"{asset_id['name']}:{asset_id['value']}"
        encoded_asset = (
            encode_identifier(asset_string)
            if self._client._encode_discovery_asset_ids
            else asset_string
        )
        await self._request_async(
            "DELETE",
            f"/lookup/shells/{encoded_aas}/{encoded_asset}",
        )

    def get_asset_links(
        self,
        aas_id: str,
    ) -> list[dict[str, str]]:
        """
        Get all asset identifiers linked to an AAS.

        Args:
            aas_id: The identifier of the AAS

        Returns:
            List of asset identifier dicts

        Raises:
            ResourceNotFoundError: If AAS not found
        """
        encoded_id = encode_identifier(aas_id)
        response = self._request("GET", f"/lookup/shells/{encoded_id}")

        if response is None:
            return []

        # Response is typically a list of specificAssetId objects
        if isinstance(response, list):
            return response
        return response.get("specificAssetIds", response.get("result", []))

    async def get_asset_links_async(
        self,
        aas_id: str,
    ) -> list[dict[str, str]]:
        """Async version of get_asset_links()."""
        encoded_id = encode_identifier(aas_id)
        response = await self._request_async("GET", f"/lookup/shells/{encoded_id}")

        if response is None:
            return []

        if isinstance(response, list):
            return response
        return response.get("specificAssetIds", response.get("result", []))

    def _parse_string_paginated_response(
        self,
        response: dict | list | None,
    ) -> PaginatedResult[str]:
        """Parse paginated response containing string IDs."""
        if response is None:
            return PaginatedResult(items=[], has_more=False)

        if isinstance(response, list):
            return PaginatedResult(items=response, has_more=False)

        result_list = response.get("result", [])
        paging_metadata = response.get("paging_metadata", {})
        cursor = paging_metadata.get("cursor")
        has_more = cursor is not None

        return PaginatedResult(items=result_list, cursor=cursor, has_more=has_more)
