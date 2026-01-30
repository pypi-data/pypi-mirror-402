"""
AAS Registry endpoint implementation.

Provides operations for AAS Descriptors in the registry:
- GET /shell-descriptors → list()
- POST /shell-descriptors → create()
- GET /shell-descriptors/{id} → get()
- PUT /shell-descriptors/{id} → update()
- DELETE /shell-descriptors/{id} → delete()
- GET /shell-descriptors/{id}/submodel-descriptors → list_submodel_descriptors()
- POST /shell-descriptors/{id}/submodel-descriptors → add_submodel_descriptor()
- GET /shell-descriptors/{id}/submodel-descriptors/{smId} → get_submodel_descriptor()
- PUT /shell-descriptors/{id}/submodel-descriptors/{smId} → update_submodel_descriptor()
- DELETE /shell-descriptors/{id}/submodel-descriptors/{smId} → remove_submodel_descriptor()
"""

from __future__ import annotations

from typing import Any

from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.pagination import PaginatedResult

# Registry uses descriptor objects, not BaSyx model objects
# These are plain dicts following the AAS Part 2 descriptor schema


class AASRegistryEndpoint(BaseEndpoint):
    """
    AAS Registry endpoint for managing AAS Descriptors.

    Note: Registry endpoints work with descriptor dicts, not BaSyx model objects,
    as descriptors have a different schema than the AAS metamodel objects.

    Example:
        # List all AAS descriptors
        result = client.aas_registry.list()

        # Get a specific AAS descriptor
        descriptor = client.aas_registry.get("urn:example:aas:123")

        # Create a new AAS descriptor
        descriptor = {
            "id": "urn:example:aas:456",
            "idShort": "MyAAS",
            "endpoints": [{"interface": "AAS-3.0", "protocolInformation": {...}}],
        }
        created = client.aas_registry.create(descriptor)
    """

    def list(
        self,
        limit: int = 100,
        cursor: str | None = None,
        asset_type: str | None = None,
        asset_kind: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """
        List AAS Descriptors.

        Args:
            limit: Maximum number of items to return
            cursor: Pagination cursor
            asset_type: Filter by asset type
            asset_kind: Filter by asset kind (Instance, Type)

        Returns:
            PaginatedResult containing descriptor dicts
        """
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if asset_type:
            params["assetType"] = asset_type
        if asset_kind:
            params["assetKind"] = asset_kind

        response = self._request("GET", "/shell-descriptors", params=params)
        return self._parse_paginated_response(response)

    async def list_async(
        self,
        limit: int = 100,
        cursor: str | None = None,
        asset_type: str | None = None,
        asset_kind: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """Async version of list()."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if asset_type:
            params["assetType"] = asset_type
        if asset_kind:
            params["assetKind"] = asset_kind

        response = await self._request_async("GET", "/shell-descriptors", params=params)
        return self._parse_paginated_response(response)

    def get(self, aas_id: str) -> dict[str, Any]:
        """
        Get a specific AAS Descriptor by ID.

        Args:
            aas_id: The identifier of the AAS

        Returns:
            AAS Descriptor dict

        Raises:
            ResourceNotFoundError: If descriptor not found
        """
        encoded_id = encode_identifier(aas_id)
        response = self._request("GET", f"/shell-descriptors/{encoded_id}")
        return response or {}

    async def get_async(self, aas_id: str) -> dict[str, Any]:
        """Async version of get()."""
        encoded_id = encode_identifier(aas_id)
        response = await self._request_async("GET", f"/shell-descriptors/{encoded_id}")
        return response or {}

    def create(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new AAS Descriptor.

        Args:
            descriptor: The AAS descriptor to create

        Returns:
            The created descriptor

        Raises:
            ConflictError: If descriptor with same ID already exists
            BadRequestError: If descriptor data is invalid
        """
        response = self._request("POST", "/shell-descriptors", json=descriptor)
        return response or descriptor

    async def create_async(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        """Async version of create()."""
        response = await self._request_async("POST", "/shell-descriptors", json=descriptor)
        return response or descriptor

    def update(self, aas_id: str, descriptor: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing AAS Descriptor.

        Args:
            aas_id: The identifier of the AAS
            descriptor: The updated descriptor

        Returns:
            The updated descriptor

        Raises:
            ResourceNotFoundError: If descriptor not found
            BadRequestError: If descriptor data is invalid
        """
        encoded_id = encode_identifier(aas_id)
        response = self._request("PUT", f"/shell-descriptors/{encoded_id}", json=descriptor)
        return response or descriptor

    async def update_async(self, aas_id: str, descriptor: dict[str, Any]) -> dict[str, Any]:
        """Async version of update()."""
        encoded_id = encode_identifier(aas_id)
        response = await self._request_async(
            "PUT",
            f"/shell-descriptors/{encoded_id}",
            json=descriptor,
        )
        return response or descriptor

    def delete(self, aas_id: str) -> None:
        """
        Delete an AAS Descriptor.

        Args:
            aas_id: The identifier of the AAS

        Raises:
            ResourceNotFoundError: If descriptor not found
        """
        encoded_id = encode_identifier(aas_id)
        self._request("DELETE", f"/shell-descriptors/{encoded_id}")

    async def delete_async(self, aas_id: str) -> None:
        """Async version of delete()."""
        encoded_id = encode_identifier(aas_id)
        await self._request_async("DELETE", f"/shell-descriptors/{encoded_id}")

    # Submodel Descriptors within AAS

    def list_submodel_descriptors(
        self,
        aas_id: str,
        limit: int = 100,
        cursor: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """
        List submodel descriptors for an AAS.

        Args:
            aas_id: The identifier of the AAS
            limit: Maximum number of items to return
            cursor: Pagination cursor

        Returns:
            PaginatedResult containing submodel descriptor dicts
        """
        encoded_id = encode_identifier(aas_id)
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        response = self._request(
            "GET",
            f"/shell-descriptors/{encoded_id}/submodel-descriptors",
            params=params,
        )
        return self._parse_paginated_response(response)

    async def list_submodel_descriptors_async(
        self,
        aas_id: str,
        limit: int = 100,
        cursor: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """Async version of list_submodel_descriptors()."""
        encoded_id = encode_identifier(aas_id)
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        response = await self._request_async(
            "GET",
            f"/shell-descriptors/{encoded_id}/submodel-descriptors",
            params=params,
        )
        return self._parse_paginated_response(response)

    def get_submodel_descriptor(self, aas_id: str, submodel_id: str) -> dict[str, Any]:
        """
        Get a specific submodel descriptor.

        Args:
            aas_id: The identifier of the AAS
            submodel_id: The identifier of the submodel

        Returns:
            Submodel descriptor dict
        """
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        response = self._request(
            "GET",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
        )
        return response or {}

    async def get_submodel_descriptor_async(
        self,
        aas_id: str,
        submodel_id: str,
    ) -> dict[str, Any]:
        """Async version of get_submodel_descriptor()."""
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        response = await self._request_async(
            "GET",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
        )
        return response or {}

    def add_submodel_descriptor(
        self,
        aas_id: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Add a submodel descriptor to an AAS.

        Args:
            aas_id: The identifier of the AAS
            descriptor: The submodel descriptor to add

        Returns:
            The added descriptor
        """
        encoded_id = encode_identifier(aas_id)
        response = self._request(
            "POST",
            f"/shell-descriptors/{encoded_id}/submodel-descriptors",
            json=descriptor,
        )
        return response or descriptor

    async def add_submodel_descriptor_async(
        self,
        aas_id: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        """Async version of add_submodel_descriptor()."""
        encoded_id = encode_identifier(aas_id)
        response = await self._request_async(
            "POST",
            f"/shell-descriptors/{encoded_id}/submodel-descriptors",
            json=descriptor,
        )
        return response or descriptor

    def update_submodel_descriptor(
        self,
        aas_id: str,
        submodel_id: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update a submodel descriptor.

        Args:
            aas_id: The identifier of the AAS
            submodel_id: The identifier of the submodel
            descriptor: The updated descriptor

        Returns:
            The updated descriptor
        """
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        response = self._request(
            "PUT",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
            json=descriptor,
        )
        return response or descriptor

    async def update_submodel_descriptor_async(
        self,
        aas_id: str,
        submodel_id: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        """Async version of update_submodel_descriptor()."""
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        response = await self._request_async(
            "PUT",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
            json=descriptor,
        )
        return response or descriptor

    def remove_submodel_descriptor(self, aas_id: str, submodel_id: str) -> None:
        """
        Remove a submodel descriptor from an AAS.

        Args:
            aas_id: The identifier of the AAS
            submodel_id: The identifier of the submodel to remove
        """
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        self._request(
            "DELETE",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
        )

    async def remove_submodel_descriptor_async(self, aas_id: str, submodel_id: str) -> None:
        """Async version of remove_submodel_descriptor()."""
        encoded_aas_id = encode_identifier(aas_id)
        encoded_sm_id = encode_identifier(submodel_id)
        await self._request_async(
            "DELETE",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
        )

    def _parse_paginated_response(
        self,
        response: dict | list | None,
    ) -> PaginatedResult[dict[str, Any]]:
        """Parse paginated response from API."""
        if response is None:
            return PaginatedResult(items=[], has_more=False)

        if isinstance(response, list):
            return PaginatedResult(items=response, has_more=False)

        result_list = response.get("result", [])
        paging_metadata = response.get("paging_metadata", {})
        cursor = paging_metadata.get("cursor")
        has_more = cursor is not None

        return PaginatedResult(items=result_list, cursor=cursor, has_more=has_more)
