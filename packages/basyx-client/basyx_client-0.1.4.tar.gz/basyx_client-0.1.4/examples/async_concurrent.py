#!/usr/bin/env python3
"""Async concurrent operations with basyx-client.

This example demonstrates:
- Async context managers
- Concurrent request execution
- Rate-limited operations with semaphores
- Async pagination

Prerequisites:
    pip install basyx-client
    # Start BaSyx server on localhost:8081
"""

import asyncio
from basyx_client import AASClient, ResourceNotFoundError
from basyx_client.pagination import iterate_pages_async

BASE_URL = "http://localhost:8081"


async def basic_async() -> None:
    """Basic async operations."""
    print("1. Basic async operations...")

    async with AASClient(BASE_URL) as client:
        # Async list
        result = await client.shells.list_async(limit=10)
        print(f"   Found {len(result.result)} shells")

        # Async get (if any shells exist)
        if result.result:
            shell = await client.shells.get_async(result.result[0].id)
            print(f"   First shell: {shell.id_short}")


async def concurrent_fetching() -> None:
    """Fetch multiple resources concurrently."""
    print("\n2. Concurrent fetching...")

    async with AASClient(BASE_URL) as client:
        # Get all submodel IDs
        result = await client.submodels.list_async(limit=20)
        ids = [sm.id for sm in result.result]

        if not ids:
            print("   No submodels found")
            return

        print(f"   Fetching {len(ids)} submodels concurrently...")

        # Fetch all concurrently
        tasks = [client.submodels.get_async(id) for id in ids]
        submodels = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = 0
        for sm in submodels:
            if isinstance(sm, Exception):
                print(f"   Error: {sm}")
            else:
                success_count += 1
                elements = sm.submodel_element or []
                print(f"   - {sm.id_short}: {len(elements)} elements")

        print(f"   Successfully fetched {success_count}/{len(ids)} submodels")


async def rate_limited_requests() -> None:
    """Use semaphore for rate limiting."""
    print("\n3. Rate-limited concurrent requests...")

    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent

    async def fetch_with_limit(client: AASClient, sm_id: str) -> tuple[str, int]:
        async with semaphore:
            try:
                sm = await client.submodels.get_async(sm_id)
                return (sm.id_short, len(sm.submodel_element or []))
            except Exception as e:
                return (sm_id, -1)

    async with AASClient(BASE_URL) as client:
        result = await client.submodels.list_async(limit=10)
        ids = [sm.id for sm in result.result]

        if not ids:
            print("   No submodels to fetch")
            return

        print(f"   Fetching {len(ids)} submodels with max 3 concurrent...")

        tasks = [fetch_with_limit(client, id) for id in ids]
        results = await asyncio.gather(*tasks)

        for name, count in results:
            if count >= 0:
                print(f"   - {name}: {count} elements")
            else:
                print(f"   - {name}: FAILED")


async def async_pagination() -> None:
    """Iterate through pages asynchronously."""
    print("\n4. Async pagination...")

    async with AASClient(BASE_URL) as client:
        count = 0
        async for shell in iterate_pages_async(client.shells.list_async, limit=5):
            count += 1
            print(f"   {count}. {shell.id_short}: {shell.id}")
            if count >= 10:  # Limit output
                print("   ... (stopping at 10)")
                break

        print(f"   Total processed: {count}")


async def multi_server_comparison() -> None:
    """Compare data between servers (simulated)."""
    print("\n5. Multi-client pattern (simulated with same server)...")

    # In practice, these would be different servers
    async with AASClient(BASE_URL) as client1, AASClient(BASE_URL) as client2:
        r1, r2 = await asyncio.gather(
            client1.shells.list_async(limit=5),
            client2.submodels.list_async(limit=5),
        )

        print(f"   Server 1 shells: {len(r1.result)}")
        print(f"   Server 2 submodels: {len(r2.result)}")


async def main() -> None:
    """Run all async examples."""
    print("=== basyx-client Async Examples ===\n")

    await basic_async()
    await concurrent_fetching()
    await rate_limited_requests()
    await async_pagination()
    await multi_server_comparison()

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
