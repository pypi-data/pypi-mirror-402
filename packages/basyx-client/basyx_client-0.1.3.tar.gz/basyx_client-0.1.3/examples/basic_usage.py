#!/usr/bin/env python3
"""
Basic usage example for basyx-client.

This example demonstrates:
- Creating an AAS client
- Listing, creating, and retrieving AAS
- Working with submodels
- Accessing submodel element values
- Error handling

Prerequisites:
- BaSyx AAS Repository running at http://localhost:8081
- BaSyx Submodel Repository running at http://localhost:8082

Start with: docker compose up -d
"""

from basyx.aas import model

from basyx_client import AASClient
from basyx_client.exceptions import ConflictError, ResourceNotFoundError


def main() -> None:
    # Create a client for the AAS Repository
    # The client handles all identifier encoding automatically
    with AASClient("http://localhost:8081") as aas_client:
        print("=== AAS Repository Operations ===\n")

        # List existing AAS
        print("Listing all AAS...")
        result = aas_client.shells.list(limit=10)
        print(f"Found {len(result.items)} AAS")
        for aas in result.items:
            print(f"  - {aas.id_short}: {aas.id}")

        # Create a new AAS
        print("\nCreating a new AAS...")
        new_aas = model.AssetAdministrationShell(
            id_="https://example.org/aas/machine-001",
            id_short="Machine001",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id="https://example.org/assets/machine-001",
            ),
        )

        try:
            created_aas = aas_client.shells.create(new_aas)
            print(f"Created AAS: {created_aas.id_short} ({created_aas.id})")
        except ConflictError:
            print("AAS already exists, retrieving it instead...")
            created_aas = aas_client.shells.get("https://example.org/aas/machine-001")

        # Get asset information
        print("\nRetrieving asset information...")
        asset_info = aas_client.shells.get_asset_info(created_aas.id)
        print(f"Asset Kind: {asset_info.asset_kind}")
        print(f"Global Asset ID: {asset_info.global_asset_id}")

    # Create a client for the Submodel Repository
    with AASClient("http://localhost:8082") as sm_client:
        print("\n=== Submodel Repository Operations ===\n")

        # Create a submodel with elements
        print("Creating a submodel...")
        submodel = model.Submodel(
            id_="https://example.org/submodels/operational-data-001",
            id_short="OperationalData",
            submodel_element={
                model.Property(
                    id_short="Temperature",
                    value_type=model.datatypes.Double,
                    value=25.5,
                ),
                model.Property(
                    id_short="Status",
                    value_type=model.datatypes.String,
                    value="Running",
                ),
                model.SubmodelElementCollection(
                    id_short="Sensors",
                    value={
                        model.Property(
                            id_short="Sensor1",
                            value_type=model.datatypes.Double,
                            value=100.0,
                        ),
                    },
                ),
            },
        )

        try:
            created_sm = sm_client.submodels.create(submodel)
            print(f"Created Submodel: {created_sm.id_short}")
        except ConflictError:
            print("Submodel already exists, retrieving it...")
            created_sm = sm_client.submodels.get(submodel.id)

        # Access submodel element values
        print("\nReading element values...")

        # Get Temperature value
        temp = sm_client.submodels.elements.get_value(
            created_sm.id,
            "Temperature",
        )
        print(f"Temperature: {temp}")

        # Get nested value using dot notation
        sensor1 = sm_client.submodels.elements.get_value(
            created_sm.id,
            "Sensors.Sensor1",
        )
        print(f"Sensors.Sensor1: {sensor1}")

        # Update a value
        print("\nUpdating Temperature to 30.0...")
        sm_client.submodels.elements.set_value(
            created_sm.id,
            "Temperature",
            30.0,
        )

        # Verify the update
        new_temp = sm_client.submodels.elements.get_value(
            created_sm.id,
            "Temperature",
        )
        print(f"New Temperature: {new_temp}")

    print("\n=== Error Handling ===\n")

    with AASClient("http://localhost:8081") as client:
        # Try to get a non-existent AAS
        try:
            client.shells.get("https://example.org/aas/nonexistent")
        except ResourceNotFoundError as e:
            print(f"Caught expected error: {e.message}")
            print(f"Status code: {e.status_code}")

    print("\nDone!")


if __name__ == "__main__":
    main()
