# Basic CRUD Operations

This guide demonstrates basic Create, Read, Update, Delete operations.

## AAS Shells

### List Shells

```python
from basyx_client import AASClient

with AASClient("http://localhost:8081") as client:
    result = client.shells.list(limit=10)
    for shell in result.result:
        print(f"ID: {shell.id}")
        print(f"  idShort: {shell.id_short}")
        print(f"  Asset: {shell.asset_information.global_asset_id}")
```

### Get a Shell

```python
with AASClient("http://localhost:8081") as client:
    shell = client.shells.get("urn:example:aas:motor-001")
    print(f"AAS: {shell.id_short}")

    # Get submodel references
    refs = client.shells.get_submodel_refs(shell.id)
    print(f"Submodels: {len(refs)}")
```

### Create a Shell

```python
aas_data = {
    "id": "urn:example:aas:new-motor",
    "idShort": "NewMotor",
    "assetInformation": {
        "assetKind": "Instance",
        "globalAssetId": "urn:example:asset:new-motor"
    }
}

with AASClient("http://localhost:8081") as client:
    shell = client.shells.create(aas_data)
    print(f"Created: {shell.id}")
```

### Delete a Shell

```python
with AASClient("http://localhost:8081") as client:
    client.shells.delete("urn:example:aas:old-motor")
    print("Deleted successfully")
```

## Submodels

### List and Filter

```python
with AASClient("http://localhost:8081") as client:
    # List all
    result = client.submodels.list()

    # Filter by semantic ID
    nameplates = client.submodels.list(
        semantic_id="https://admin-shell.io/idta/nameplate/2/0"
    )
```

### Get Submodel

```python
with AASClient("http://localhost:8081") as client:
    sm = client.submodels.get("urn:example:submodel:sensors")

    print(f"Submodel: {sm.id_short}")
    for elem in sm.submodel_element or []:
        print(f"  - {elem.id_short}: {type(elem).__name__}")
```

### Create Submodel

```python
submodel_data = {
    "id": "urn:example:submodel:new-sensors",
    "idShort": "NewSensors",
    "submodelElements": [
        {
            "modelType": "Property",
            "idShort": "Temperature",
            "valueType": "xs:double",
            "value": "20.0"
        }
    ]
}

with AASClient("http://localhost:8081") as client:
    sm = client.submodels.create(submodel_data)
    print(f"Created: {sm.id}")
```

## Submodel Elements

### Read Element Value

```python
with AASClient("http://localhost:8081") as client:
    # Simple property
    temp = client.submodels.elements.get_value(
        "urn:example:submodel:sensors",
        "Temperature"
    )
    print(f"Temperature: {temp}")

    # Nested element
    motor_speed = client.submodels.elements.get_value(
        "urn:example:submodel:operational",
        "Motor.Speed"
    )
```

### Update Element Value

```python
with AASClient("http://localhost:8081") as client:
    # Set numeric value
    client.submodels.elements.set_value(
        "urn:example:submodel:sensors",
        "Setpoint",
        25.5
    )

    # Set string value
    client.submodels.elements.set_value(
        "urn:example:submodel:operational",
        "Status",
        "Running"
    )
```

### Create Element

```python
new_element = {
    "modelType": "Property",
    "idShort": "Humidity",
    "valueType": "xs:double",
    "value": "60.0"
}

with AASClient("http://localhost:8081") as client:
    elem = client.submodels.elements.create(
        "urn:example:submodel:sensors",
        new_element
    )
    print(f"Created: {elem.id_short}")
```

### Delete Element

```python
with AASClient("http://localhost:8081") as client:
    client.submodels.elements.delete(
        "urn:example:submodel:sensors",
        "OldSensor"
    )
```

## Complete Example

```python
"""Complete CRUD workflow example."""

from basyx_client import AASClient, ResourceNotFoundError

BASE_URL = "http://localhost:8081"

def main():
    with AASClient(BASE_URL) as client:
        # Create AAS
        aas = client.shells.create({
            "id": "urn:demo:aas:1",
            "idShort": "DemoAAS",
            "assetInformation": {
                "assetKind": "Instance",
                "globalAssetId": "urn:demo:asset:1"
            }
        })
        print(f"Created AAS: {aas.id}")

        # Create Submodel
        sm = client.submodels.create({
            "id": "urn:demo:submodel:1",
            "idShort": "DemoSubmodel",
            "submodelElements": [
                {
                    "modelType": "Property",
                    "idShort": "Counter",
                    "valueType": "xs:int",
                    "value": "0"
                }
            ]
        })
        print(f"Created Submodel: {sm.id}")

        # Read value
        counter = client.submodels.elements.get_value(sm.id, "Counter")
        print(f"Counter value: {counter}")

        # Update value
        client.submodels.elements.set_value(sm.id, "Counter", 42)
        print("Updated counter to 42")

        # Verify update
        counter = client.submodels.elements.get_value(sm.id, "Counter")
        print(f"New counter value: {counter}")

        # Cleanup
        client.submodels.delete(sm.id)
        client.shells.delete(aas.id)
        print("Cleaned up resources")

if __name__ == "__main__":
    main()
```
