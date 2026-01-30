"""
AASX Server endpoint implementation.

Provides operations for AASX package management:
- GET /packages → list()
- POST /packages → upload()
- GET /packages/{id} → get()
- PUT /packages/{id} → update()
- DELETE /packages/{id} → delete()
- GET /packages/{id}/aas/{aasId} → get_aas_from_package()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from basyx.aas import model

from basyx_client.encoding import encode_identifier
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.pagination import PaginatedResult
from basyx_client.serialization import deserialize_aas


class AASXServerEndpoint(BaseEndpoint):
    """
    AASX Server endpoint for managing AASX packages.

    AASX packages are ZIP archives containing AAS, Submodels, and related files.

    Example:
        # List all packages
        result = client.packages.list()

        # Upload a new package
        package_id = client.packages.upload("/path/to/my-package.aasx")

        # Get an AAS from a package
        aas = client.packages.get_aas_from_package("package-123", "urn:example:aas:456")
    """

    def _encode_package_id(self, package_id: str) -> str:
        """Encode package IDs if configured to do so."""
        if self._client._encode_package_id:
            return encode_identifier(package_id)
        return package_id

    def list(
        self,
        limit: int = 100,
        cursor: str | None = None,
        aas_id: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """
        List AASX packages.

        Args:
            limit: Maximum number of items to return
            cursor: Pagination cursor
            aas_id: Filter by AAS ID contained in package

        Returns:
            PaginatedResult containing package metadata dicts
        """
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if aas_id:
            params["aasId"] = encode_identifier(aas_id)

        response = self._request("GET", "/packages", params=params)
        return self._parse_paginated_response(response)

    async def list_async(
        self,
        limit: int = 100,
        cursor: str | None = None,
        aas_id: str | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """Async version of list()."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if aas_id:
            params["aasId"] = encode_identifier(aas_id)

        response = await self._request_async("GET", "/packages", params=params)
        return self._parse_paginated_response(response)

    def get(self, package_id: str) -> bytes:
        """
        Download an AASX package.

        Args:
            package_id: The identifier of the package

        Returns:
            Package content as bytes

        Raises:
            ResourceNotFoundError: If package not found
        """
        encoded_id = self._encode_package_id(package_id)
        url = f"{self._client.base_url}/packages/{encoded_id}"

        response = self._client._sync_client.get(url)
        if not response.is_success:
            from basyx_client.exceptions import map_status_to_exception

            raise map_status_to_exception(
                response.status_code,
                f"Failed to download package: {response.text[:200]}",
                url,
            )
        return response.content

    async def get_async(self, package_id: str) -> bytes:
        """Async version of get()."""
        encoded_id = self._encode_package_id(package_id)
        url = f"{self._client.base_url}/packages/{encoded_id}"

        response = await self._client._async_client.get(url)
        if not response.is_success:
            from basyx_client.exceptions import map_status_to_exception

            raise map_status_to_exception(
                response.status_code,
                f"Failed to download package: {response.text[:200]}",
                url,
            )
        return response.content

    def upload(
        self,
        file_path: str | Path,
        aas_ids: list[str] | None = None,
    ) -> str:
        """
        Upload an AASX package.

        Args:
            file_path: Path to the AASX file
            aas_ids: Optional list of AAS IDs to associate with the package

        Returns:
            Package ID of the uploaded package

        Raises:
            BadRequestError: If package data is invalid
        """
        file_path = Path(file_path)

        with open(file_path, "rb") as f:
            content = f.read()

        files = {
            "file": (file_path.name, content, "application/asset-administration-shell-package")
        }
        params: dict[str, list[str]] = {}
        if aas_ids is not None:
            params["aasIds"] = [encode_identifier(aid) for aid in aas_ids]

        url = f"{self._client.base_url}/packages"
        response = self._client._sync_client.post(
            url, files=files, params=params if params else None
        )

        if not response.is_success:
            from basyx_client.exceptions import map_status_to_exception

            raise map_status_to_exception(
                response.status_code,
                f"Failed to upload package: {response.text[:200]}",
                url,
            )

        result = response.json() if response.content else {}
        return result.get("packageId", "")

    async def upload_async(
        self,
        file_path: str | Path,
        aas_ids: list[str] | None = None,
    ) -> str:
        """Async version of upload()."""
        file_path = Path(file_path)

        with open(file_path, "rb") as f:
            content = f.read()

        files = {
            "file": (file_path.name, content, "application/asset-administration-shell-package")
        }
        params: dict[str, list[str]] = {}
        if aas_ids is not None:
            params["aasIds"] = [encode_identifier(aid) for aid in aas_ids]

        url = f"{self._client.base_url}/packages"
        response = await self._client._async_client.post(
            url,
            files=files,
            params=params if params else None,
        )

        if not response.is_success:
            from basyx_client.exceptions import map_status_to_exception

            raise map_status_to_exception(
                response.status_code,
                f"Failed to upload package: {response.text[:200]}",
                url,
            )

        result = response.json() if response.content else {}
        return result.get("packageId", "")

    def update(
        self,
        package_id: str,
        file_path: str | Path,
    ) -> None:
        """
        Update an existing AASX package.

        Args:
            package_id: The identifier of the package to update
            file_path: Path to the new AASX file

        Raises:
            ResourceNotFoundError: If package not found
            BadRequestError: If package data is invalid
        """
        file_path = Path(file_path)
        encoded_id = self._encode_package_id(package_id)

        with open(file_path, "rb") as f:
            content = f.read()

        files = {
            "file": (file_path.name, content, "application/asset-administration-shell-package")
        }

        url = f"{self._client.base_url}/packages/{encoded_id}"
        response = self._client._sync_client.put(url, files=files)

        if not response.is_success:
            from basyx_client.exceptions import map_status_to_exception

            raise map_status_to_exception(
                response.status_code,
                f"Failed to update package: {response.text[:200]}",
                url,
            )

    async def update_async(
        self,
        package_id: str,
        file_path: str | Path,
    ) -> None:
        """Async version of update()."""
        file_path = Path(file_path)
        encoded_id = self._encode_package_id(package_id)

        with open(file_path, "rb") as f:
            content = f.read()

        files = {
            "file": (file_path.name, content, "application/asset-administration-shell-package")
        }

        url = f"{self._client.base_url}/packages/{encoded_id}"
        response = await self._client._async_client.put(url, files=files)

        if not response.is_success:
            from basyx_client.exceptions import map_status_to_exception

            raise map_status_to_exception(
                response.status_code,
                f"Failed to update package: {response.text[:200]}",
                url,
            )

    def delete(self, package_id: str) -> None:
        """
        Delete an AASX package.

        Args:
            package_id: The identifier of the package to delete

        Raises:
            ResourceNotFoundError: If package not found
        """
        encoded_id = self._encode_package_id(package_id)
        self._request("DELETE", f"/packages/{encoded_id}")

    async def delete_async(self, package_id: str) -> None:
        """Async version of delete()."""
        encoded_id = self._encode_package_id(package_id)
        await self._request_async("DELETE", f"/packages/{encoded_id}")

    def get_aas_from_package(
        self,
        package_id: str,
        aas_id: str,
    ) -> model.AssetAdministrationShell:
        """
        Get an AAS from a specific package.

        Args:
            package_id: The identifier of the package
            aas_id: The identifier of the AAS within the package

        Returns:
            AssetAdministrationShell object

        Raises:
            ResourceNotFoundError: If package or AAS not found
        """
        encoded_pkg_id = self._encode_package_id(package_id)
        encoded_aas_id = encode_identifier(aas_id)
        response = self._request("GET", f"/packages/{encoded_pkg_id}/aas/{encoded_aas_id}")
        return deserialize_aas(response)

    async def get_aas_from_package_async(
        self,
        package_id: str,
        aas_id: str,
    ) -> model.AssetAdministrationShell:
        """Async version of get_aas_from_package()."""
        encoded_pkg_id = self._encode_package_id(package_id)
        encoded_aas_id = encode_identifier(aas_id)
        response = await self._request_async(
            "GET",
            f"/packages/{encoded_pkg_id}/aas/{encoded_aas_id}",
        )
        return deserialize_aas(response)

    def download_to_file(self, package_id: str, destination: str | Path) -> Path:
        """
        Download an AASX package and save to a file.

        Args:
            package_id: The identifier of the package
            destination: Destination file path

        Returns:
            Path to the downloaded file
        """
        content = self.get(package_id)
        dest_path = Path(destination)
        dest_path.write_bytes(content)
        return dest_path

    async def download_to_file_async(self, package_id: str, destination: str | Path) -> Path:
        """Async version of download_to_file()."""
        content = await self.get_async(package_id)
        dest_path = Path(destination)
        dest_path.write_bytes(content)
        return dest_path

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
