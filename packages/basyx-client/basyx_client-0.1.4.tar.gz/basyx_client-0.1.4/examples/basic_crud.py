#!/usr/bin/env python3
"""Basic CRUD operations with basyx-client.

This example demonstrates:
- Creating AAS shells and submodels
- Reading and listing resources
- Updating element values
- Deleting resources

Prerequisites:
    pip install basyx-client
    # Start BaSyx server on localhost:8081
"""

from basyx_client import AASClient, ResourceNotFoundError

BASE_URL = "http://localhost:8081"


def main() -> None:
    """Run basic CRUD examples."""
    with AASClient(BASE_URL) as client:
        print("=== basyx-client Basic CRUD Example ===\n")

        # --- CREATE ---
        print("1. Creating resources...")

        # Create AAS
        aas_data = {
            "id": "urn:example:aas:demo-motor",
            "idShort": "DemoMotor",
            "assetInformation": {
                "assetKind": "Instance",
                "globalAssetId": "urn:example:asset:demo-motor",
            },
        }

        try:
            aas = client.shells.create(aas_data)
            print(f"   Created AAS: {aas.id}")
        except Exception as e:
            print(f"   AAS creation failed (may already exist): {e}")

        # Create Submodel
        submodel_data = {
            "id": "urn:example:submodel:demo-sensors",
            "idShort": "DemoSensors",
            "submodelElements": [
                {
                    "modelType": "Property",
                    "idShort": "Temperature",
                    "valueType": "xs:double",
                    "value": "25.0",
                },
                {
                    "modelType": "Property",
                    "idShort": "Humidity",
                    "valueType": "xs:double",
                    "value": "60.0",
                },
                {
                    "modelType": "Property",
                    "idShort": "Status",
                    "valueType": "xs:string",
                    "value": "Running",
                },
            ],
        }

        try:
            sm = client.submodels.create(submodel_data)
            print(f"   Created Submodel: {sm.id}")
        except Exception as e:
            print(f"   Submodel creation failed (may already exist): {e}")

        # --- READ ---
        print("\n2. Reading resources...")

        # List shells
        result = client.shells.list(limit=5)
        print(f"   Found {len(result.result)} AAS shells:")
        for shell in result.result:
            print(f"      - {shell.id_short}: {shell.id}")

        # Get specific submodel
        try:
            sm = client.submodels.get("urn:example:submodel:demo-sensors")
            print(f"\n   Submodel '{sm.id_short}' elements:")
            for elem in sm.submodel_element or []:
                print(f"      - {elem.id_short}: {type(elem).__name__}")
        except ResourceNotFoundError:
            print("   Submodel not found")

        # Read element values
        print("\n3. Reading element values...")
        try:
            temp = client.submodels.elements.get_value(
                "urn:example:submodel:demo-sensors", "Temperature"
            )
            print(f"   Temperature: {temp}")

            status = client.submodels.elements.get_value(
                "urn:example:submodel:demo-sensors", "Status"
            )
            print(f"   Status: {status}")
        except ResourceNotFoundError:
            print("   Elements not found")

        # --- UPDATE ---
        print("\n4. Updating values...")
        try:
            # Update temperature
            client.submodels.elements.set_value(
                "urn:example:submodel:demo-sensors", "Temperature", 28.5
            )
            print("   Updated Temperature to 28.5")

            # Update status
            client.submodels.elements.set_value(
                "urn:example:submodel:demo-sensors", "Status", "Overheating"
            )
            print("   Updated Status to 'Overheating'")

            # Verify updates
            temp = client.submodels.elements.get_value(
                "urn:example:submodel:demo-sensors", "Temperature"
            )
            print(f"   Verified Temperature: {temp}")
        except ResourceNotFoundError:
            print("   Update failed - elements not found")

        # --- DELETE ---
        print("\n5. Cleanup (deleting resources)...")
        try:
            client.submodels.delete("urn:example:submodel:demo-sensors")
            print("   Deleted submodel")
        except ResourceNotFoundError:
            print("   Submodel already deleted")

        try:
            client.shells.delete("urn:example:aas:demo-motor")
            print("   Deleted AAS")
        except ResourceNotFoundError:
            print("   AAS already deleted")

        print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
