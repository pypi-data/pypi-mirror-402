"""Integration tests for Submodel Repository endpoint.

These tests require a running BaSyx Submodel Repository service.
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
class TestSubmodelRepositoryIntegration:
    """Integration tests for Submodel Repository operations."""

    def test_list_submodels(self, submodel_client: AASClient) -> None:
        """Test listing submodels."""
        result = submodel_client.submodels.list(limit=10)
        assert hasattr(result, "items")
        assert isinstance(result.items, list)

    def test_create_and_get_submodel(
        self, submodel_client: AASClient, sample_submodel_identifier: str
    ) -> None:
        """Test creating and retrieving a submodel."""
        # Create a submodel with a property
        sm = model.Submodel(
            id_=sample_submodel_identifier,
            id_short="TestSubmodel",
            submodel_element={
                model.Property(
                    id_short="Temperature",
                    value_type=model.datatypes.Double,
                    value=25.5,
                ),
            },
        )

        try:
            # Create
            created = submodel_client.submodels.create(sm)
            assert isinstance(created, model.Submodel)
            assert created.id_short == "TestSubmodel"

            # Get
            retrieved = submodel_client.submodels.get(sample_submodel_identifier)
            assert isinstance(retrieved, model.Submodel)
            assert retrieved.id == sample_submodel_identifier

        finally:
            # Cleanup
            try:
                submodel_client.submodels.delete(sample_submodel_identifier)
            except Exception:
                pass

    def test_update_submodel(
        self, submodel_client: AASClient, sample_submodel_identifier: str
    ) -> None:
        """Test updating a submodel."""
        sm = model.Submodel(
            id_=sample_submodel_identifier,
            id_short="OriginalSubmodel",
        )

        try:
            submodel_client.submodels.create(sm)

            # Update
            sm.id_short = "UpdatedSubmodel"
            updated = submodel_client.submodels.update(sample_submodel_identifier, sm)

            assert updated.id_short == "UpdatedSubmodel"

        finally:
            try:
                submodel_client.submodels.delete(sample_submodel_identifier)
            except Exception:
                pass

    def test_delete_submodel(
        self, submodel_client: AASClient, sample_submodel_identifier: str
    ) -> None:
        """Test deleting a submodel."""
        from basyx_client.exceptions import ResourceNotFoundError

        sm = model.Submodel(
            id_=sample_submodel_identifier,
            id_short="ToDeleteSubmodel",
        )
        submodel_client.submodels.create(sm)

        # Delete
        submodel_client.submodels.delete(sample_submodel_identifier)

        # Verify deleted
        with pytest.raises(ResourceNotFoundError):
            submodel_client.submodels.get(sample_submodel_identifier)

    def test_submodel_not_found(self, submodel_client: AASClient) -> None:
        """Test that ResourceNotFoundError is raised for non-existent submodel."""
        from basyx_client.exceptions import ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError):
            submodel_client.submodels.get("urn:non:existent:submodel:12345")


@pytest.mark.integration
class TestSubmodelElementsIntegration:
    """Integration tests for Submodel Element operations."""

    def test_get_element(self, submodel_client: AASClient, sample_submodel_identifier: str) -> None:
        """Test getting a submodel element."""
        # Create submodel with element
        sm = model.Submodel(
            id_=sample_submodel_identifier,
            id_short="ElementTestSubmodel",
            submodel_element={
                model.Property(
                    id_short="TestProperty",
                    value_type=model.datatypes.String,
                    value="test_value",
                ),
            },
        )

        try:
            submodel_client.submodels.create(sm)

            # Get element
            element = submodel_client.submodels.elements.get(
                sample_submodel_identifier, "TestProperty"
            )
            assert isinstance(element, model.SubmodelElement)

        finally:
            try:
                submodel_client.submodels.delete(sample_submodel_identifier)
            except Exception:
                pass

    def test_get_and_set_value(
        self, submodel_client: AASClient, sample_submodel_identifier: str
    ) -> None:
        """Test getting and setting element values."""
        sm = model.Submodel(
            id_=sample_submodel_identifier,
            id_short="ValueTestSubmodel",
            submodel_element={
                model.Property(
                    id_short="Counter",
                    value_type=model.datatypes.Int,
                    value=0,
                ),
            },
        )

        try:
            submodel_client.submodels.create(sm)

            # Get initial value (API returns string representation)
            initial = submodel_client.submodels.elements.get_value(
                sample_submodel_identifier, "Counter"
            )
            assert initial == "0"

            # Set new value
            submodel_client.submodels.elements.set_value(sample_submodel_identifier, "Counter", 42)

            # Verify update (API returns string representation)
            updated = submodel_client.submodels.elements.get_value(
                sample_submodel_identifier, "Counter"
            )
            assert updated == "42"

        finally:
            try:
                submodel_client.submodels.delete(sample_submodel_identifier)
            except Exception:
                pass

    def test_list_elements(
        self, submodel_client: AASClient, sample_submodel_identifier: str
    ) -> None:
        """Test listing submodel elements."""
        sm = model.Submodel(
            id_=sample_submodel_identifier,
            id_short="ListTestSubmodel",
            submodel_element={
                model.Property(
                    id_short="Prop1",
                    value_type=model.datatypes.String,
                    value="a",
                ),
                model.Property(
                    id_short="Prop2",
                    value_type=model.datatypes.String,
                    value="b",
                ),
            },
        )

        try:
            submodel_client.submodels.create(sm)

            # List elements
            result = submodel_client.submodels.elements.list(sample_submodel_identifier)
            assert len(result.items) >= 2

        finally:
            try:
                submodel_client.submodels.delete(sample_submodel_identifier)
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.asyncio
class TestSubmodelAsyncIntegration:
    """Async integration tests for Submodel Repository."""

    async def test_list_submodels_async(self, submodel_client: AASClient) -> None:
        """Test async listing of submodels."""
        async with AASClient(submodel_client.base_url) as client:
            result = await client.submodels.list_async(limit=10)
            assert hasattr(result, "items")
            assert isinstance(result.items, list)
