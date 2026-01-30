"""Integration tests for AAS Registry endpoint.

These tests require a running BaSyx AAS Registry service.
Start with: docker compose up -d
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from basyx_client import AASClient

if TYPE_CHECKING:
    pass


@pytest.mark.integration
class TestAASRegistryIntegration:
    """Integration tests for AAS Registry operations."""

    def test_list_shell_descriptors(self, registry_client: AASClient) -> None:
        """Test listing AAS shell descriptors."""
        result = registry_client.aas_registry.list(limit=10)
        assert hasattr(result, "items")
        assert isinstance(result.items, list)

    def test_create_and_get_descriptor(
        self, registry_client: AASClient, sample_aas_identifier: str
    ) -> None:
        """Test creating and retrieving an AAS descriptor."""
        # Create a descriptor (dict since we don't have typed descriptors)
        descriptor = {
            "id": sample_aas_identifier,
            "idShort": "TestAASDescriptor",
            "assetKind": "Instance",
            "assetType": "urn:example:asset:type",
            "endpoints": [
                {
                    "interface": "AAS-3.0",
                    "protocolInformation": {
                        "href": "http://localhost:8081/api/v3.0/shells/" + sample_aas_identifier,
                        "endpointProtocol": "HTTP",
                    },
                }
            ],
        }

        try:
            # Create
            created = registry_client.aas_registry.create(descriptor)
            assert isinstance(created, dict)
            assert created.get("idShort") == "TestAASDescriptor"

            # Get
            retrieved = registry_client.aas_registry.get(sample_aas_identifier)
            assert isinstance(retrieved, dict)
            assert retrieved.get("id") == sample_aas_identifier

        finally:
            # Cleanup
            try:
                registry_client.aas_registry.delete(sample_aas_identifier)
            except Exception:
                pass

    def test_update_descriptor(
        self, registry_client: AASClient, sample_aas_identifier: str
    ) -> None:
        """Test updating an AAS descriptor."""
        descriptor = {
            "id": sample_aas_identifier,
            "idShort": "OriginalDescriptor",
            "assetKind": "Instance",
            "endpoints": [
                {
                    "interface": "AAS-3.0",
                    "protocolInformation": {
                        "href": f"http://localhost:8081/shells/{sample_aas_identifier}",
                        "endpointProtocol": "HTTP",
                    },
                }
            ],
        }

        try:
            registry_client.aas_registry.create(descriptor)

            # Update
            descriptor["idShort"] = "UpdatedDescriptor"
            updated = registry_client.aas_registry.update(sample_aas_identifier, descriptor)

            assert updated.get("idShort") == "UpdatedDescriptor"

        finally:
            try:
                registry_client.aas_registry.delete(sample_aas_identifier)
            except Exception:
                pass

    def test_delete_descriptor(
        self, registry_client: AASClient, sample_aas_identifier: str
    ) -> None:
        """Test deleting an AAS descriptor."""
        from basyx_client.exceptions import ResourceNotFoundError

        descriptor = {
            "id": sample_aas_identifier,
            "idShort": "ToDeleteDescriptor",
            "assetKind": "Instance",
            "endpoints": [
                {
                    "interface": "AAS-3.0",
                    "protocolInformation": {
                        "href": f"http://localhost:8081/shells/{sample_aas_identifier}",
                        "endpointProtocol": "HTTP",
                    },
                }
            ],
        }
        registry_client.aas_registry.create(descriptor)

        # Delete
        registry_client.aas_registry.delete(sample_aas_identifier)

        # Verify deleted
        with pytest.raises(ResourceNotFoundError):
            registry_client.aas_registry.get(sample_aas_identifier)

    def test_descriptor_not_found(self, registry_client: AASClient) -> None:
        """Test that ResourceNotFoundError is raised for non-existent descriptor."""
        from basyx_client.exceptions import ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError):
            registry_client.aas_registry.get("urn:non:existent:descriptor:12345")


@pytest.mark.integration
class TestSubmodelRegistryIntegration:
    """Integration tests for Submodel Registry operations."""

    def test_list_submodel_descriptors(self, submodel_registry_client: AASClient) -> None:
        """Test listing submodel descriptors."""
        result = submodel_registry_client.submodel_registry.list(limit=10)
        assert hasattr(result, "items")
        assert isinstance(result.items, list)

    def test_create_and_get_submodel_descriptor(
        self, submodel_registry_client: AASClient, sample_submodel_identifier: str
    ) -> None:
        """Test creating and retrieving a submodel descriptor."""
        descriptor = {
            "id": sample_submodel_identifier,
            "idShort": "TestSubmodelDescriptor",
            "endpoints": [
                {
                    "interface": "SUBMODEL-3.0",
                    "protocolInformation": {
                        "href": f"http://localhost:8082/submodels/{sample_submodel_identifier}",
                        "endpointProtocol": "HTTP",
                    },
                }
            ],
        }

        try:
            # Create
            created = submodel_registry_client.submodel_registry.create(descriptor)
            assert isinstance(created, dict)

            # Get
            retrieved = submodel_registry_client.submodel_registry.get(sample_submodel_identifier)
            assert isinstance(retrieved, dict)
            assert retrieved.get("id") == sample_submodel_identifier

        finally:
            try:
                submodel_registry_client.submodel_registry.delete(sample_submodel_identifier)
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.asyncio
class TestRegistryAsyncIntegration:
    """Async integration tests for Registry endpoints."""

    async def test_list_descriptors_async(self, registry_client: AASClient) -> None:
        """Test async listing of descriptors."""
        async with AASClient(registry_client.base_url) as client:
            result = await client.aas_registry.list_async(limit=10)
            assert hasattr(result, "items")
            assert isinstance(result.items, list)
