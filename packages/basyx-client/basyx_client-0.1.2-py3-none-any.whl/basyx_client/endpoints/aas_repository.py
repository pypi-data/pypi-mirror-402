"""
AAS Repository endpoint implementation.

Provides CRUD operations for Asset Administration Shells:
- GET /shells → list()
- POST /shells → create()
- GET /shells/{id} → get()
- PUT /shells/{id} → update()
- DELETE /shells/{id} → delete()
- GET /shells/{id}/submodel-refs → list_submodel_refs()
- POST /shells/{id}/submodel-refs → add_submodel_ref()
- DELETE /shells/{id}/submodel-refs/{ref} → remove_submodel_ref()
- GET /shells/{id}/asset-information → get_asset_info()
- PUT /shells/{id}/asset-information → update_asset_info()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from basyx.aas import model

from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.pagination import PaginatedResult
from basyx_client.serialization import (
    deserialize_aas,
    deserialize_asset_information,
    deserialize_reference,
    serialize,
)

if TYPE_CHECKING:
    pass


class AASRepositoryEndpoint(BaseEndpoint):
    """
    AAS Repository endpoint for managing Asset Administration Shells.

    Example:
        # List all shells
        result = client.shells.list()
        for aas in result.items:
            print(aas.id_short)

        # Get a specific shell
        aas = client.shells.get("urn:example:aas:123")

        # Create a new shell
        new_aas = model.AssetAdministrationShell(...)
        created = client.shells.create(new_aas)
    """

    def list(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        asset_ids: list[str] | None = None,
    ) -> PaginatedResult[model.AssetAdministrationShell]:
        """
        List Asset Administration Shells.

        Args:
            limit: Maximum number of items to return (default 100)
            cursor: Pagination cursor from previous response
            id_short: Filter by idShort (optional)
            asset_ids: Filter by asset IDs (optional)

        Returns:
            PaginatedResult containing AssetAdministrationShell objects
        """
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if asset_ids:
            # Asset IDs are base64url encoded in query
            params["assetIds"] = [encode_identifier(aid) for aid in asset_ids]

        response = self._request("GET", "/shells", params=params)
        return self._parse_paginated_response(response)

    async def list_async(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        asset_ids: list[str] | None = None,
    ) -> PaginatedResult[model.AssetAdministrationShell]:
        """Async version of list()."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if asset_ids is not None:
            params["assetIds"] = [encode_identifier(aid) for aid in asset_ids]

        response = await self._request_async("GET", "/shells", params=params)
        return self._parse_paginated_response(response)

    def get(self, aas_id: str) -> model.AssetAdministrationShell:
        """
        Get a specific Asset Administration Shell by ID.

        Args:
            aas_id: The identifier of the AAS (will be automatically base64url encoded)

        Returns:
            AssetAdministrationShell object

        Raises:
            ResourceNotFoundError: If AAS not found
        """
        encoded_id = encode_identifier(aas_id)
        response = self._request("GET", f"/shells/{encoded_id}")
        return deserialize_aas(response)

    async def get_async(self, aas_id: str) -> model.AssetAdministrationShell:
        """Async version of get()."""
        encoded_id = encode_identifier(aas_id)
        response = await self._request_async("GET", f"/shells/{encoded_id}")
        return deserialize_aas(response)

    def create(
        self,
        aas: model.AssetAdministrationShell,
    ) -> model.AssetAdministrationShell:
        """
        Create a new Asset Administration Shell.

        Args:
            aas: The AAS to create

        Returns:
            The created AssetAdministrationShell (may include server-generated fields)

        Raises:
            ConflictError: If AAS with same ID already exists
            BadRequestError: If AAS data is invalid
        """
        payload = serialize(aas)
        response = self._request("POST", "/shells", json=payload)
        return deserialize_aas(response)

    async def create_async(
        self,
        aas: model.AssetAdministrationShell,
    ) -> model.AssetAdministrationShell:
        """Async version of create()."""
        payload = serialize(aas)
        response = await self._request_async("POST", "/shells", json=payload)
        return deserialize_aas(response)

    def update(
        self,
        aas_id: str,
        aas: model.AssetAdministrationShell,
    ) -> model.AssetAdministrationShell:
        """
        Update an existing Asset Administration Shell.

        Args:
            aas_id: The identifier of the AAS to update
            aas: The updated AAS

        Returns:
            The updated AssetAdministrationShell

        Raises:
            ResourceNotFoundError: If AAS not found
            BadRequestError: If AAS data is invalid
        """
        encoded_id = encode_identifier(aas_id)
        payload = serialize(aas)
        response = self._request("PUT", f"/shells/{encoded_id}", json=payload)
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return self.get(aas_id)
        return deserialize_aas(response)

    async def update_async(
        self,
        aas_id: str,
        aas: model.AssetAdministrationShell,
    ) -> model.AssetAdministrationShell:
        """Async version of update()."""
        encoded_id = encode_identifier(aas_id)
        payload = serialize(aas)
        response = await self._request_async("PUT", f"/shells/{encoded_id}", json=payload)
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return await self.get_async(aas_id)
        return deserialize_aas(response)

    def delete(self, aas_id: str) -> None:
        """
        Delete an Asset Administration Shell.

        Args:
            aas_id: The identifier of the AAS to delete

        Raises:
            ResourceNotFoundError: If AAS not found
        """
        encoded_id = encode_identifier(aas_id)
        self._request("DELETE", f"/shells/{encoded_id}")

    async def delete_async(self, aas_id: str) -> None:
        """Async version of delete()."""
        encoded_id = encode_identifier(aas_id)
        await self._request_async("DELETE", f"/shells/{encoded_id}")

    # Submodel References

    def list_submodel_refs(self, aas_id: str) -> list[model.Reference]:
        """
        List submodel references for an AAS.

        Args:
            aas_id: The identifier of the AAS

        Returns:
            List of Reference objects pointing to submodels
        """
        encoded_id = encode_identifier(aas_id)
        response = self._request("GET", f"/shells/{encoded_id}/submodel-refs")

        if response is None:
            return []

        # Response might be paginated or just a list
        items = response.get("result", response) if isinstance(response, dict) else response
        return [deserialize_reference(ref) for ref in items]

    async def list_submodel_refs_async(self, aas_id: str) -> list[model.Reference]:
        """Async version of list_submodel_refs()."""
        encoded_id = encode_identifier(aas_id)
        response = await self._request_async("GET", f"/shells/{encoded_id}/submodel-refs")

        if response is None:
            return []

        items = response.get("result", response) if isinstance(response, dict) else response
        return [deserialize_reference(ref) for ref in items]

    def add_submodel_ref(self, aas_id: str, ref: model.Reference) -> model.Reference:
        """
        Add a submodel reference to an AAS.

        Args:
            aas_id: The identifier of the AAS
            ref: The submodel reference to add

        Returns:
            The added Reference
        """
        encoded_id = encode_identifier(aas_id)
        payload = serialize(ref)
        response = self._request("POST", f"/shells/{encoded_id}/submodel-refs", json=payload)
        return deserialize_reference(response)

    async def add_submodel_ref_async(
        self,
        aas_id: str,
        ref: model.Reference,
    ) -> model.Reference:
        """Async version of add_submodel_ref()."""
        encoded_id = encode_identifier(aas_id)
        payload = serialize(ref)
        response = await self._request_async(
            "POST",
            f"/shells/{encoded_id}/submodel-refs",
            json=payload,
        )
        return deserialize_reference(response)

    def remove_submodel_ref(self, aas_id: str, submodel_id: str) -> None:
        """
        Remove a submodel reference from an AAS.

        Args:
            aas_id: The identifier of the AAS
            submodel_id: The identifier of the submodel to remove
        """
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        self._request("DELETE", f"/shells/{encoded_aas_id}/submodel-refs/{encoded_sm_id}")

    async def remove_submodel_ref_async(self, aas_id: str, submodel_id: str) -> None:
        """Async version of remove_submodel_ref()."""
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        await self._request_async(
            "DELETE",
            f"/shells/{encoded_aas_id}/submodel-refs/{encoded_sm_id}",
        )

    # Asset Information

    def get_asset_info(self, aas_id: str) -> model.AssetInformation:
        """
        Get the asset information for an AAS.

        Args:
            aas_id: The identifier of the AAS

        Returns:
            AssetInformation object
        """
        encoded_id = encode_identifier(aas_id)
        response = self._request("GET", f"/shells/{encoded_id}/asset-information")
        return deserialize_asset_information(response)

    async def get_asset_info_async(self, aas_id: str) -> model.AssetInformation:
        """Async version of get_asset_info()."""
        encoded_id = encode_identifier(aas_id)
        response = await self._request_async("GET", f"/shells/{encoded_id}/asset-information")
        return deserialize_asset_information(response)

    def update_asset_info(
        self,
        aas_id: str,
        asset_info: model.AssetInformation,
    ) -> model.AssetInformation:
        """
        Update the asset information for an AAS.

        Args:
            aas_id: The identifier of the AAS
            asset_info: The updated asset information

        Returns:
            The updated AssetInformation
        """
        encoded_id = encode_identifier(aas_id)
        payload = serialize(asset_info)
        response = self._request("PUT", f"/shells/{encoded_id}/asset-information", json=payload)
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return self.get_asset_info(aas_id)
        return deserialize_asset_information(response)

    async def update_asset_info_async(
        self,
        aas_id: str,
        asset_info: model.AssetInformation,
    ) -> model.AssetInformation:
        """Async version of update_asset_info()."""
        encoded_id = encode_identifier(aas_id)
        payload = serialize(asset_info)
        response = await self._request_async(
            "PUT",
            f"/shells/{encoded_id}/asset-information",
            json=payload,
        )
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return await self.get_asset_info_async(aas_id)
        return deserialize_asset_information(response)

    def _parse_paginated_response(
        self,
        response: dict | list | None,
    ) -> PaginatedResult[model.AssetAdministrationShell]:
        """Parse paginated response from API."""
        if response is None:
            return PaginatedResult(items=[], has_more=False)

        if isinstance(response, list):
            # Direct list response (no pagination metadata)
            items = [deserialize_aas(item) for item in response]
            return PaginatedResult(items=items, has_more=False)

        # Paginated response with metadata
        result_list = response.get("result", [])
        items = [deserialize_aas(item) for item in result_list]

        paging_metadata = response.get("paging_metadata", {})
        cursor = paging_metadata.get("cursor")
        has_more = cursor is not None

        return PaginatedResult(items=items, cursor=cursor, has_more=has_more)
