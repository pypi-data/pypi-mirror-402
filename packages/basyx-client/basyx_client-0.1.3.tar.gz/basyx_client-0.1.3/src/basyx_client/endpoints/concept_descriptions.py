"""
Concept Description endpoint implementation.

Provides CRUD operations for Concept Descriptions:
- GET /concept-descriptions → list()
- POST /concept-descriptions → create()
- GET /concept-descriptions/{id} → get()
- PUT /concept-descriptions/{id} → update()
- DELETE /concept-descriptions/{id} → delete()
"""

from __future__ import annotations

from basyx.aas import model

from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.pagination import PaginatedResult
from basyx_client.serialization import deserialize_concept_description, serialize


class ConceptDescriptionEndpoint(BaseEndpoint):
    """
    Concept Description endpoint for managing ConceptDescriptions.

    Example:
        # List all concept descriptions
        result = client.concept_descriptions.list()

        # Get a specific concept description
        cd = client.concept_descriptions.get("urn:example:cd:temperature")

        # Create a new concept description
        new_cd = model.ConceptDescription(...)
        created = client.concept_descriptions.create(new_cd)
    """

    def list(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        is_case_of: str | None = None,
        data_specification_ref: str | None = None,
    ) -> PaginatedResult[model.ConceptDescription]:
        """
        List Concept Descriptions.

        Args:
            limit: Maximum number of items to return
            cursor: Pagination cursor
            id_short: Filter by idShort
            is_case_of: Filter by isCaseOf reference
            data_specification_ref: Filter by data specification reference

        Returns:
            PaginatedResult containing ConceptDescription objects
        """
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if is_case_of:
            params["isCaseOf"] = encode_identifier(is_case_of)
        if data_specification_ref:
            params["dataSpecificationRef"] = encode_identifier(data_specification_ref)

        response = self._request("GET", "/concept-descriptions", params=params)
        return self._parse_paginated_response(response)

    async def list_async(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        is_case_of: str | None = None,
        data_specification_ref: str | None = None,
    ) -> PaginatedResult[model.ConceptDescription]:
        """Async version of list()."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if is_case_of:
            params["isCaseOf"] = encode_identifier(is_case_of)
        if data_specification_ref:
            params["dataSpecificationRef"] = encode_identifier(data_specification_ref)

        response = await self._request_async("GET", "/concept-descriptions", params=params)
        return self._parse_paginated_response(response)

    def get(self, cd_id: str) -> model.ConceptDescription:
        """
        Get a specific Concept Description by ID.

        Args:
            cd_id: The identifier of the concept description

        Returns:
            ConceptDescription object

        Raises:
            ResourceNotFoundError: If concept description not found
        """
        encoded_id = encode_identifier(cd_id)
        response = self._request("GET", f"/concept-descriptions/{encoded_id}")
        return deserialize_concept_description(response)

    async def get_async(self, cd_id: str) -> model.ConceptDescription:
        """Async version of get()."""
        encoded_id = encode_identifier(cd_id)
        response = await self._request_async("GET", f"/concept-descriptions/{encoded_id}")
        return deserialize_concept_description(response)

    def create(self, cd: model.ConceptDescription) -> model.ConceptDescription:
        """
        Create a new Concept Description.

        Args:
            cd: The concept description to create

        Returns:
            The created ConceptDescription

        Raises:
            ConflictError: If concept description with same ID already exists
            BadRequestError: If concept description data is invalid
        """
        payload = serialize(cd)
        response = self._request("POST", "/concept-descriptions", json=payload)
        return deserialize_concept_description(response)

    async def create_async(self, cd: model.ConceptDescription) -> model.ConceptDescription:
        """Async version of create()."""
        payload = serialize(cd)
        response = await self._request_async("POST", "/concept-descriptions", json=payload)
        return deserialize_concept_description(response)

    def update(self, cd_id: str, cd: model.ConceptDescription) -> model.ConceptDescription:
        """
        Update an existing Concept Description.

        Args:
            cd_id: The identifier of the concept description to update
            cd: The updated concept description

        Returns:
            The updated ConceptDescription

        Raises:
            ResourceNotFoundError: If concept description not found
            BadRequestError: If concept description data is invalid
        """
        encoded_id = encode_identifier(cd_id)
        payload = serialize(cd)
        response = self._request("PUT", f"/concept-descriptions/{encoded_id}", json=payload)
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return self.get(cd_id)
        return deserialize_concept_description(response)

    async def update_async(
        self,
        cd_id: str,
        cd: model.ConceptDescription,
    ) -> model.ConceptDescription:
        """Async version of update()."""
        encoded_id = encode_identifier(cd_id)
        payload = serialize(cd)
        response = await self._request_async(
            "PUT",
            f"/concept-descriptions/{encoded_id}",
            json=payload,
        )
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return await self.get_async(cd_id)
        return deserialize_concept_description(response)

    def delete(self, cd_id: str) -> None:
        """
        Delete a Concept Description.

        Args:
            cd_id: The identifier of the concept description to delete

        Raises:
            ResourceNotFoundError: If concept description not found
        """
        encoded_id = encode_identifier(cd_id)
        self._request("DELETE", f"/concept-descriptions/{encoded_id}")

    async def delete_async(self, cd_id: str) -> None:
        """Async version of delete()."""
        encoded_id = encode_identifier(cd_id)
        await self._request_async("DELETE", f"/concept-descriptions/{encoded_id}")

    def _parse_paginated_response(
        self,
        response: dict | list | None,
    ) -> PaginatedResult[model.ConceptDescription]:
        """Parse paginated response from API."""
        if response is None:
            return PaginatedResult(items=[], has_more=False)

        if isinstance(response, list):
            items = [deserialize_concept_description(item) for item in response]
            return PaginatedResult(items=items, has_more=False)

        result_list = response.get("result", [])
        items = [deserialize_concept_description(item) for item in result_list]

        paging_metadata = response.get("paging_metadata", {})
        cursor = paging_metadata.get("cursor")
        has_more = cursor is not None

        return PaginatedResult(items=items, cursor=cursor, has_more=has_more)
