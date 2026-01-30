"""Integration tests for AAS Repository endpoint.

These tests require a running BaSyx AAS Repository service.
Start with: docker compose up -d
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from basyx.aas import model

from basyx_client import AASClient

if TYPE_CHECKING:
    pass


@pytest.mark.integration
class TestAASRepositoryIntegration:
    """Integration tests for AAS Repository operations."""

    def test_list_shells(self, aas_client: AASClient) -> None:
        """Test listing AAS shells."""
        result = aas_client.shells.list(limit=10)
        assert hasattr(result, "items")
        assert isinstance(result.items, list)

    def test_create_and_get_shell(self, aas_client: AASClient, sample_aas_identifier: str) -> None:
        """Test creating and retrieving an AAS."""
        # Create an AAS
        aas = model.AssetAdministrationShell(
            id_=sample_aas_identifier,
            id_short="TestAAS",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:example:asset:{sample_aas_identifier}",
            ),
        )

        try:
            # Create
            created = aas_client.shells.create(aas)
            assert isinstance(created, model.AssetAdministrationShell)
            assert created.id_short == "TestAAS"

            # Get
            retrieved = aas_client.shells.get(sample_aas_identifier)
            assert isinstance(retrieved, model.AssetAdministrationShell)
            assert retrieved.id == sample_aas_identifier
            assert retrieved.id_short == "TestAAS"

        finally:
            # Cleanup
            try:
                aas_client.shells.delete(sample_aas_identifier)
            except Exception:
                pass

    def test_update_shell(self, aas_client: AASClient, sample_aas_identifier: str) -> None:
        """Test updating an AAS."""
        # Create initial AAS
        aas = model.AssetAdministrationShell(
            id_=sample_aas_identifier,
            id_short="OriginalName",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:example:asset:{sample_aas_identifier}",
            ),
        )

        try:
            aas_client.shells.create(aas)

            # Update
            aas.id_short = "UpdatedName"
            updated = aas_client.shells.update(sample_aas_identifier, aas)

            assert updated.id_short == "UpdatedName"

        finally:
            try:
                aas_client.shells.delete(sample_aas_identifier)
            except Exception:
                pass

    def test_delete_shell(self, aas_client: AASClient, sample_aas_identifier: str) -> None:
        """Test deleting an AAS."""
        from basyx_client.exceptions import ResourceNotFoundError

        # Create
        aas = model.AssetAdministrationShell(
            id_=sample_aas_identifier,
            id_short="ToDelete",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:example:asset:{sample_aas_identifier}",
            ),
        )
        aas_client.shells.create(aas)

        # Delete
        aas_client.shells.delete(sample_aas_identifier)

        # Verify deleted
        with pytest.raises(ResourceNotFoundError):
            aas_client.shells.get(sample_aas_identifier)

    def test_shell_not_found(self, aas_client: AASClient) -> None:
        """Test that ResourceNotFoundError is raised for non-existent AAS."""
        from basyx_client.exceptions import ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError):
            aas_client.shells.get("urn:non:existent:aas:12345")

    def test_pagination(self, aas_client: AASClient) -> None:
        """Test pagination of list results."""
        result = aas_client.shells.list(limit=1)
        # Just verify the pagination metadata is present
        assert hasattr(result, "cursor")
        assert hasattr(result, "has_more")


@pytest.mark.integration
@pytest.mark.asyncio
class TestAASRepositoryAsyncIntegration:
    """Async integration tests for AAS Repository."""

    async def test_list_shells_async(self, aas_client: AASClient) -> None:
        """Test async listing of AAS shells."""
        async with AASClient(aas_client.base_url) as client:
            result = await client.shells.list_async(limit=10)
            assert hasattr(result, "items")
            assert isinstance(result.items, list)

    async def test_create_and_get_async(
        self, aas_client: AASClient, sample_aas_identifier: str
    ) -> None:
        """Test async create and get operations."""
        aas = model.AssetAdministrationShell(
            id_=sample_aas_identifier,
            id_short="AsyncTestAAS",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:example:asset:{sample_aas_identifier}",
            ),
        )

        async with AASClient(aas_client.base_url) as client:
            try:
                # Create
                created = await client.shells.create_async(aas)
                assert isinstance(created, model.AssetAdministrationShell)

                # Get
                retrieved = await client.shells.get_async(sample_aas_identifier)
                assert retrieved.id == sample_aas_identifier

            finally:
                try:
                    await client.shells.delete_async(sample_aas_identifier)
                except Exception:
                    pass
