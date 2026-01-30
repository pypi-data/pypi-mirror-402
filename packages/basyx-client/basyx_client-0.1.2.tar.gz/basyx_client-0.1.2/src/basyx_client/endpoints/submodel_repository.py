"""
Submodel Repository endpoint implementation.

Provides CRUD operations for Submodels and SubmodelElements:
- GET /submodels → list()
- POST /submodels → create()
- GET /submodels/{id} → get()
- PUT /submodels/{id} → update()
- DELETE /submodels/{id} → delete()
- GET /submodels/{id}/submodel-elements → elements.list()
- GET /submodels/{id}/submodel-elements/{path} → elements.get()
- GET /submodels/{id}/submodel-elements/{path}/$value → elements.get_value()
- PATCH /submodels/{id}/submodel-elements/{path}/$value → elements.set_value()
- POST /submodels/{id}/submodel-elements/{path} → elements.create()
- PUT /submodels/{id}/submodel-elements/{path} → elements.update()
- DELETE /submodels/{id}/submodel-elements/{path} → elements.delete()
- POST /submodels/{id}/submodel-elements/{path}/invoke → elements.invoke()
- POST /submodels/{id}/submodel-elements/{path}/invoke-async → elements.invoke_async()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from basyx.aas import model

from basyx_client.encoding import encode_id_short_path, encode_identifier
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.pagination import PaginatedResult
from basyx_client.serialization import (
    deserialize_submodel,
    deserialize_submodel_element,
    serialize,
    serialize_value,
)

if TYPE_CHECKING:
    from basyx_client.client import AASClient


class SubmodelElementsEndpoint(BaseEndpoint):
    """
    Nested endpoint for submodel element operations.

    Accessed via SubmodelRepositoryEndpoint.elements
    """

    def __init__(self, client: AASClient, parent: SubmodelRepositoryEndpoint) -> None:
        super().__init__(client)
        self._parent = parent

    def list(
        self,
        submodel_id: str,
        limit: int = 100,
        cursor: str | None = None,
        level: str = "deep",
    ) -> PaginatedResult[model.SubmodelElement]:
        """
        List submodel elements.

        Args:
            submodel_id: The identifier of the submodel
            limit: Maximum number of items to return
            cursor: Pagination cursor
            level: Depth level ("deep" or "core")

        Returns:
            PaginatedResult containing SubmodelElement objects
        """
        encoded_id = encode_identifier(submodel_id)
        params = {"limit": limit, "level": level}
        if cursor:
            params["cursor"] = cursor

        response = self._request("GET", f"/submodels/{encoded_id}/submodel-elements", params=params)
        return self._parse_paginated_response(response)

    async def list_async(
        self,
        submodel_id: str,
        limit: int = 100,
        cursor: str | None = None,
        level: str = "deep",
    ) -> PaginatedResult[model.SubmodelElement]:
        """Async version of list()."""
        encoded_id = encode_identifier(submodel_id)
        params = {"limit": limit, "level": level}
        if cursor:
            params["cursor"] = cursor

        response = await self._request_async(
            "GET",
            f"/submodels/{encoded_id}/submodel-elements",
            params=params,
        )
        return self._parse_paginated_response(response)

    def get(self, submodel_id: str, id_short_path: str) -> model.SubmodelElement:
        """
        Get a specific submodel element by path.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Path to the element (e.g., "Sensors.Temperature" or "Data[0].Value")

        Returns:
            SubmodelElement object

        Raises:
            ResourceNotFoundError: If element not found
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        response = self._request(
            "GET",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    async def get_async(self, submodel_id: str, id_short_path: str) -> model.SubmodelElement:
        """Async version of get()."""
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        response = await self._request_async(
            "GET",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    def get_value(self, submodel_id: str, id_short_path: str) -> Any:
        """
        Get the value of a submodel element.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Path to the element

        Returns:
            The element's value (type depends on element type)
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        response = self._request(
            "GET",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}/$value",
        )
        return response

    async def get_value_async(self, submodel_id: str, id_short_path: str) -> Any:
        """Async version of get_value()."""
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        response = await self._request_async(
            "GET",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}/$value",
        )
        return response

    def set_value(self, submodel_id: str, id_short_path: str, value: Any) -> None:
        """
        Set the value of a submodel element.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Path to the element
            value: The new value to set (will be converted to string for primitives)
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        json_value = serialize_value(value)
        self._request(
            "PATCH",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}/$value",
            json=json_value,
        )

    async def set_value_async(self, submodel_id: str, id_short_path: str, value: Any) -> None:
        """Async version of set_value()."""
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        json_value = serialize_value(value)
        await self._request_async(
            "PATCH",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}/$value",
            json=json_value,
        )

    def create(
        self,
        submodel_id: str,
        id_short_path: str,
        element: model.SubmodelElement,
    ) -> model.SubmodelElement:
        """
        Create a new submodel element.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Parent path where to create the element
            element: The element to create

        Returns:
            The created SubmodelElement
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        payload = serialize(element)
        response = self._request(
            "POST",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
            json=payload,
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    def create_root(
        self,
        submodel_id: str,
        element: model.SubmodelElement,
    ) -> model.SubmodelElement:
        """
        Create a new submodel element at the root.

        Args:
            submodel_id: The identifier of the submodel
            element: The element to create at the root level

        Returns:
            The created SubmodelElement
        """
        encoded_sm_id = encode_identifier(submodel_id)
        payload = serialize(element)
        response = self._request(
            "POST",
            f"/submodels/{encoded_sm_id}/submodel-elements",
            json=payload,
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    async def create_async(
        self,
        submodel_id: str,
        id_short_path: str,
        element: model.SubmodelElement,
    ) -> model.SubmodelElement:
        """Async version of create()."""
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        payload = serialize(element)
        response = await self._request_async(
            "POST",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
            json=payload,
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    async def create_root_async(
        self,
        submodel_id: str,
        element: model.SubmodelElement,
    ) -> model.SubmodelElement:
        """Async version of create_root()."""
        encoded_sm_id = encode_identifier(submodel_id)
        payload = serialize(element)
        response = await self._request_async(
            "POST",
            f"/submodels/{encoded_sm_id}/submodel-elements",
            json=payload,
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    def update(
        self,
        submodel_id: str,
        id_short_path: str,
        element: model.SubmodelElement,
    ) -> model.SubmodelElement:
        """
        Update an existing submodel element.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Path to the element
            element: The updated element

        Returns:
            The updated SubmodelElement
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        payload = serialize(element)
        response = self._request(
            "PUT",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
            json=payload,
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    async def update_async(
        self,
        submodel_id: str,
        id_short_path: str,
        element: model.SubmodelElement,
    ) -> model.SubmodelElement:
        """Async version of update()."""
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        payload = serialize(element)
        response = await self._request_async(
            "PUT",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
            json=payload,
        )
        return deserialize_submodel_element(cast("dict[str, Any]", response))

    def delete(self, submodel_id: str, id_short_path: str) -> None:
        """
        Delete a submodel element.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Path to the element
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        self._request(
            "DELETE",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
        )

    async def delete_async(self, submodel_id: str, id_short_path: str) -> None:
        """Async version of delete()."""
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)
        await self._request_async(
            "DELETE",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}",
        )

    def invoke(
        self,
        submodel_id: str,
        id_short_path: str,
        input_arguments: list[dict[str, Any]] | None = None,
        inoutput_arguments: list[dict[str, Any]] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        Invoke an operation synchronously.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Path to the operation
            input_arguments: Input arguments for the operation
            inoutput_arguments: In/out arguments for the operation
            timeout: Execution timeout in seconds

        Returns:
            Operation result containing output/inoutput arguments
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)

        payload: dict[str, Any] = {}
        if input_arguments:
            payload["inputArguments"] = input_arguments
        if inoutput_arguments:
            payload["inoutputArguments"] = inoutput_arguments

        params: dict[str, Any] = {}
        if timeout is not None:
            params["timeout"] = timeout

        response = self._request(
            "POST",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}/invoke",
            json=payload,
            params=params if params else None,
        )
        return cast("dict[str, Any]", response) if response else {}

    async def invoke_async_operation(
        self,
        submodel_id: str,
        id_short_path: str,
        input_arguments: list[dict[str, Any]] | None = None,
        inoutput_arguments: list[dict[str, Any]] | None = None,
    ) -> str:
        """
        Start an asynchronous operation invocation.

        Args:
            submodel_id: The identifier of the submodel
            id_short_path: Path to the operation
            input_arguments: Input arguments for the operation
            inoutput_arguments: In/out arguments for the operation

        Returns:
            Handle ID for checking operation status
        """
        encoded_sm_id = encode_identifier(submodel_id)
        encoded_path = encode_id_short_path(id_short_path)

        payload: dict[str, Any] = {}
        if input_arguments:
            payload["inputArguments"] = input_arguments
        if inoutput_arguments:
            payload["inoutputArguments"] = inoutput_arguments

        response = await self._request_async(
            "POST",
            f"/submodels/{encoded_sm_id}/submodel-elements/{encoded_path}/invoke-async",
            json=payload,
        )
        if response is None or isinstance(response, list):
            return ""
        return str(response.get("handleId", ""))

    def _parse_paginated_response(
        self,
        response: dict[str, Any] | list[Any] | None,
    ) -> PaginatedResult[model.SubmodelElement]:
        """Parse paginated response from API."""
        if response is None:
            return PaginatedResult(items=[], has_more=False)

        if isinstance(response, list):
            items = [
                deserialize_submodel_element(cast("dict[str, Any]", item)) for item in response
            ]
            return PaginatedResult(items=items, has_more=False)

        result_list: list[Any] = response.get("result", [])
        items = [deserialize_submodel_element(cast("dict[str, Any]", item)) for item in result_list]

        paging_metadata: dict[str, Any] = response.get("paging_metadata", {})
        cursor = paging_metadata.get("cursor")
        has_more = cursor is not None

        return PaginatedResult(items=items, cursor=cursor, has_more=has_more)


class SubmodelRepositoryEndpoint(BaseEndpoint):
    """
    Submodel Repository endpoint for managing Submodels.

    Provides access to:
    - Submodel CRUD operations
    - SubmodelElement operations via .elements

    Example:
        # List all submodels
        result = client.submodels.list()

        # Get a specific submodel
        sm = client.submodels.get("urn:example:sm:123")

        # Get a submodel element value
        value = client.submodels.elements.get_value("urn:example:sm:123", "Temperature")

        # Set a submodel element value
        client.submodels.elements.set_value("urn:example:sm:123", "Temperature", 25.5)
    """

    def __init__(self, client: AASClient) -> None:
        super().__init__(client)
        self.elements = SubmodelElementsEndpoint(client, self)

    def list(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        semantic_id: str | None = None,
    ) -> PaginatedResult[model.Submodel]:
        """
        List Submodels.

        Args:
            limit: Maximum number of items to return
            cursor: Pagination cursor
            id_short: Filter by idShort
            semantic_id: Filter by semantic ID

        Returns:
            PaginatedResult containing Submodel objects
        """
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if semantic_id:
            params["semanticId"] = encode_identifier(semantic_id)

        response = self._request("GET", "/submodels", params=params)
        return self._parse_paginated_response(response)

    async def list_async(
        self,
        limit: int = 100,
        cursor: str | None = None,
        id_short: str | None = None,
        semantic_id: str | None = None,
    ) -> PaginatedResult[model.Submodel]:
        """Async version of list()."""
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if id_short:
            params["idShort"] = id_short
        if semantic_id:
            params["semanticId"] = encode_identifier(semantic_id)

        response = await self._request_async("GET", "/submodels", params=params)
        return self._parse_paginated_response(response)

    def get(self, submodel_id: str, level: str = "deep") -> model.Submodel:
        """
        Get a specific Submodel by ID.

        Args:
            submodel_id: The identifier of the submodel
            level: Depth level ("deep" or "core")

        Returns:
            Submodel object

        Raises:
            ResourceNotFoundError: If submodel not found
        """
        encoded_id = encode_identifier(submodel_id)
        params = {"level": level}
        response = self._request("GET", f"/submodels/{encoded_id}", params=params)
        return deserialize_submodel(cast("dict[str, Any]", response))

    async def get_async(self, submodel_id: str, level: str = "deep") -> model.Submodel:
        """Async version of get()."""
        encoded_id = encode_identifier(submodel_id)
        params = {"level": level}
        response = await self._request_async("GET", f"/submodels/{encoded_id}", params=params)
        return deserialize_submodel(cast("dict[str, Any]", response))

    def create(self, submodel: model.Submodel) -> model.Submodel:
        """
        Create a new Submodel.

        Args:
            submodel: The submodel to create

        Returns:
            The created Submodel

        Raises:
            ConflictError: If submodel with same ID already exists
            BadRequestError: If submodel data is invalid
        """
        payload = serialize(submodel)
        response = self._request("POST", "/submodels", json=payload)
        return deserialize_submodel(cast("dict[str, Any]", response))

    async def create_async(self, submodel: model.Submodel) -> model.Submodel:
        """Async version of create()."""
        payload = serialize(submodel)
        response = await self._request_async("POST", "/submodels", json=payload)
        return deserialize_submodel(cast("dict[str, Any]", response))

    def update(self, submodel_id: str, submodel: model.Submodel) -> model.Submodel:
        """
        Update an existing Submodel.

        Args:
            submodel_id: The identifier of the submodel to update
            submodel: The updated submodel

        Returns:
            The updated Submodel

        Raises:
            ResourceNotFoundError: If submodel not found
            BadRequestError: If submodel data is invalid
        """
        encoded_id = encode_identifier(submodel_id)
        payload = serialize(submodel)
        response = self._request("PUT", f"/submodels/{encoded_id}", json=payload)
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return self.get(submodel_id)
        return deserialize_submodel(cast("dict[str, Any]", response))

    async def update_async(self, submodel_id: str, submodel: model.Submodel) -> model.Submodel:
        """Async version of update()."""
        encoded_id = encode_identifier(submodel_id)
        payload = serialize(submodel)
        response = await self._request_async("PUT", f"/submodels/{encoded_id}", json=payload)
        # Server returns 204 No Content on success, so re-fetch
        if response is None:
            return await self.get_async(submodel_id)
        return deserialize_submodel(cast("dict[str, Any]", response))

    def delete(self, submodel_id: str) -> None:
        """
        Delete a Submodel.

        Args:
            submodel_id: The identifier of the submodel to delete

        Raises:
            ResourceNotFoundError: If submodel not found
        """
        encoded_id = encode_identifier(submodel_id)
        self._request("DELETE", f"/submodels/{encoded_id}")

    async def delete_async(self, submodel_id: str) -> None:
        """Async version of delete()."""
        encoded_id = encode_identifier(submodel_id)
        await self._request_async("DELETE", f"/submodels/{encoded_id}")

    def _parse_paginated_response(
        self,
        response: dict[str, Any] | list[Any] | None,
    ) -> PaginatedResult[model.Submodel]:
        """Parse paginated response from API."""
        if response is None:
            return PaginatedResult(items=[], has_more=False)

        if isinstance(response, list):
            items = [deserialize_submodel(cast("dict[str, Any]", item)) for item in response]
            return PaginatedResult(items=items, has_more=False)

        result_list: list[Any] = response.get("result", [])
        items = [deserialize_submodel(cast("dict[str, Any]", item)) for item in result_list]

        paging_metadata: dict[str, Any] = response.get("paging_metadata", {})
        cursor = paging_metadata.get("cursor")
        has_more = cursor is not None

        return PaginatedResult(items=items, cursor=cursor, has_more=has_more)
