"""
Submodel Registry endpoint implementation.

Provides operations for Submodel Descriptors in the registry:
- GET /submodel-descriptors → list()
- POST /submodel-descriptors → create()
- GET /submodel-descriptors/{id} → get()
- PUT /submodel-descriptors/{id} → update()
- DELETE /submodel-descriptors/{id} → delete()
"""

from __future__ import annotations

from typing import Any

from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.pagination import PaginatedResult


class SubmodelRegistryEndpoint(BaseEndpoint):
    """
    Submodel Registry endpoint for managing Submodel Descriptors.

    Note: Registry endpoints work with descriptor dicts, not BaSyx model objects,
    as descriptors have a different schema than the AAS metamodel objects.

    Example:
        # List all submodel descriptors
        result = client.submodel_registry.list()

        # Get a specific submodel descriptor
        descriptor = client.submodel_registry.get("urn:example:sm:123")

        # Create a new submodel descriptor
        descriptor = {
            "id": "urn:example:sm:456",
            "idShort": "MySubmodel",
            "endpoints": [{"interface": "SUBMODEL-3.0", "protocolInformation": {...}}],
        }
        created = client.submodel_registry.create(descriptor)
    """

    def list(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        semantic_id: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """
        List Submodel Descriptors.

        Args:
            limit: Maximum number of items to return
            cursor: Pagination cursor
            id_short: Filter by idShort
            semantic_id: Filter by semantic ID

        Returns:
            PaginatedResult containing descriptor dicts
        """
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if semantic_id:
            params["semanticId"] = encode_identifier(semantic_id)

        response = self._request("GET", "/submodel-descriptors", params=params)
        return self._parse_paginated_response(response)

    async def list_async(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        semantic_id: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """Async version of list()."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if semantic_id:
            params["semanticId"] = encode_identifier(semantic_id)

        response = await self._request_async("GET", "/submodel-descriptors", params=params)
        return self._parse_paginated_response(response)

    def get(self, submodel_id: str) -> dict[str, Any]:
        """
        Get a specific Submodel Descriptor by ID.

        Args:
            submodel_id: The identifier of the submodel

        Returns:
            Submodel Descriptor dict

        Raises:
            ResourceNotFoundError: If descriptor not found
        """
        encoded_id = encode_identifier(submodel_id)
        response = self._request("GET", f"/submodel-descriptors/{encoded_id}")
        return response or {}

    async def get_async(self, submodel_id: str) -> dict[str, Any]:
        """Async version of get()."""
        encoded_id = encode_identifier(submodel_id)
        response = await self._request_async("GET", f"/submodel-descriptors/{encoded_id}")
        return response or {}

    def create(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new Submodel Descriptor.

        Args:
            descriptor: The submodel descriptor to create

        Returns:
            The created descriptor

        Raises:
            ConflictError: If descriptor with same ID already exists
            BadRequestError: If descriptor data is invalid
        """
        response = self._request("POST", "/submodel-descriptors", json=descriptor)
        return response or descriptor

    async def create_async(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        """Async version of create()."""
        response = await self._request_async("POST", "/submodel-descriptors", json=descriptor)
        return response or descriptor

    def update(self, submodel_id: str, descriptor: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing Submodel Descriptor.

        Args:
            submodel_id: The identifier of the submodel
            descriptor: The updated descriptor

        Returns:
            The updated descriptor

        Raises:
            ResourceNotFoundError: If descriptor not found
            BadRequestError: If descriptor data is invalid
        """
        encoded_id = encode_identifier(submodel_id)
        response = self._request("PUT", f"/submodel-descriptors/{encoded_id}", json=descriptor)
        return response or descriptor

    async def update_async(
        self,
        submodel_id: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        """Async version of update()."""
        encoded_id = encode_identifier(submodel_id)
        response = await self._request_async(
            "PUT",
            f"/submodel-descriptors/{encoded_id}",
            json=descriptor,
        )
        return response or descriptor

    def delete(self, submodel_id: str) -> None:
        """
        Delete a Submodel Descriptor.

        Args:
            submodel_id: The identifier of the submodel

        Raises:
            ResourceNotFoundError: If descriptor not found
        """
        encoded_id = encode_identifier(submodel_id)
        self._request("DELETE", f"/submodel-descriptors/{encoded_id}")

    async def delete_async(self, submodel_id: str) -> None:
        """Async version of delete()."""
        encoded_id = encode_identifier(submodel_id)
        await self._request_async("DELETE", f"/submodel-descriptors/{encoded_id}")

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
