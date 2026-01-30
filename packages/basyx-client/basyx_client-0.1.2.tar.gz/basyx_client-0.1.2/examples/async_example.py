#!/usr/bin/env python3
"""
Async usage example for basyx-client.

This example demonstrates:
- Using the async API
- Concurrent operations with asyncio.gather
- Async pagination

Prerequisites:
- BaSyx AAS Repository running at http://localhost:8081
- BaSyx Submodel Repository running at http://localhost:8082

Start with: docker compose up -d
"""

import asyncio

from basyx.aas import model

from basyx_client import AASClient
from basyx_client.exceptions import ConflictError


async def create_sample_aas(client: AASClient, index: int) -> model.AssetAdministrationShell:
    """Create a sample AAS with given index."""
    aas = model.AssetAdministrationShell(
        id_=f"https://example.org/aas/async-machine-{index:03d}",
        id_short=f"AsyncMachine{index:03d}",
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=f"https://example.org/assets/machine-{index:03d}",
        ),
    )

    try:
        return await client.shells.create_async(aas)
    except ConflictError:
        return await client.shells.get_async(aas.id)


async def main() -> None:
    print("=== Async Operations Example ===\n")

    async with AASClient("http://localhost:8081") as client:
        # Create multiple AAS concurrently
        print("Creating 5 AAS concurrently...")

        # Using asyncio.gather for concurrent execution
        created_aas_list = await asyncio.gather(
            create_sample_aas(client, 1),
            create_sample_aas(client, 2),
            create_sample_aas(client, 3),
            create_sample_aas(client, 4),
            create_sample_aas(client, 5),
        )

        print(f"Created/Retrieved {len(created_aas_list)} AAS:")
        for aas in created_aas_list:
            print(f"  - {aas.id_short}")

        # Concurrent fetches
        print("\nFetching all 5 AAS concurrently...")

        fetch_tasks = [
            client.shells.get_async(f"https://example.org/aas/async-machine-{i:03d}")
            for i in range(1, 6)
        ]
        fetched_aas_list = await asyncio.gather(*fetch_tasks)

        print("Fetched AAS:")
        for aas in fetched_aas_list:
            print(f"  - {aas.id_short}: {aas.asset_information.global_asset_id}")

        # List with async
        print("\nListing all AAS (async)...")
        result = await client.shells.list_async(limit=100)
        print(f"Total AAS in repository: {len(result.items)}")

        # Async pagination
        if result.has_more:
            print(f"More pages available (cursor: {result.cursor})")

    # Example with submodel repository
    print("\n=== Async Submodel Operations ===\n")

    async with AASClient("http://localhost:8082") as sm_client:
        # Create sample submodels concurrently
        submodels = []
        for i in range(3):
            sm = model.Submodel(
                id_=f"https://example.org/submodels/async-data-{i:03d}",
                id_short=f"AsyncData{i:03d}",
                submodel_element={
                    model.Property(
                        id_short="Value",
                        value_type=model.datatypes.Int,
                        value=i * 100,
                    ),
                },
            )
            submodels.append(sm)

        async def create_or_get_sm(sm: model.Submodel) -> model.Submodel:
            try:
                return await sm_client.submodels.create_async(sm)
            except ConflictError:
                return await sm_client.submodels.get_async(sm.id)

        print("Creating 3 submodels concurrently...")
        created_sms = await asyncio.gather(*[create_or_get_sm(sm) for sm in submodels])

        print("Created/Retrieved submodels:")
        for sm in created_sms:
            print(f"  - {sm.id_short}")

        # Concurrent value reads
        print("\nReading values concurrently...")
        value_tasks = [
            sm_client.submodels.elements.get_value_async(sm.id, "Value") for sm in created_sms
        ]
        values = await asyncio.gather(*value_tasks)

        for sm, value in zip(created_sms, values):
            print(f"  - {sm.id_short}.Value = {value}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
