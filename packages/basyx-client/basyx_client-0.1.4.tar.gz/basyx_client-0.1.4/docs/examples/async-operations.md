# Async Operations

Examples of asynchronous patterns for high-performance applications.

## Basic Async

```python
import asyncio
from basyx_client import AASClient

async def main():
    async with AASClient("http://localhost:8081") as client:
        # Async list
        result = await client.shells.list_async()
        print(f"Found {len(result.result)} shells")

        # Async get
        if result.result:
            shell = await client.shells.get_async(result.result[0].id)
            print(f"First shell: {shell.id_short}")

asyncio.run(main())
```

## Concurrent Fetching

Fetch multiple resources simultaneously:

```python
import asyncio
from basyx_client import AASClient

async def main():
    async with AASClient("http://localhost:8081") as client:
        # Get all submodel IDs
        result = await client.submodels.list_async()
        ids = [sm.id for sm in result.result]

        # Fetch all submodels concurrently
        tasks = [client.submodels.get_async(id) for id in ids]
        submodels = await asyncio.gather(*tasks)

        for sm in submodels:
            elements = sm.submodel_element or []
            print(f"{sm.id_short}: {len(elements)} elements")

asyncio.run(main())
```

## Rate-Limited Requests

Control concurrency with semaphores:

```python
import asyncio
from basyx_client import AASClient

MAX_CONCURRENT = 5

async def fetch_submodel(client, semaphore, sm_id):
    async with semaphore:
        return await client.submodels.get_async(sm_id)

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with AASClient("http://localhost:8081") as client:
        result = await client.submodels.list_async()
        ids = [sm.id for sm in result.result]

        tasks = [fetch_submodel(client, semaphore, id) for id in ids]
        submodels = await asyncio.gather(*tasks)
        print(f"Fetched {len(submodels)} submodels")

asyncio.run(main())
```

## Async Pagination

```python
import asyncio
from basyx_client import AASClient
from basyx_client.pagination import iterate_pages_async

async def main():
    async with AASClient("http://localhost:8081") as client:
        count = 0
        async for shell in iterate_pages_async(client.shells.list_async):
            count += 1
            print(f"{count}. {shell.id}")

asyncio.run(main())
```

## Multi-Server Operations

Compare or sync data between servers:

```python
import asyncio
from basyx_client import AASClient

async def compare_servers(url1, url2):
    async with AASClient(url1) as c1, AASClient(url2) as c2:
        r1, r2 = await asyncio.gather(
            c1.shells.list_async(),
            c2.shells.list_async()
        )

        ids1 = {s.id for s in r1.result}
        ids2 = {s.id for s in r2.result}

        print(f"Server 1 only: {ids1 - ids2}")
        print(f"Server 2 only: {ids2 - ids1}")
        print(f"Both servers: {ids1 & ids2}")

asyncio.run(compare_servers(
    "http://server1:8081",
    "http://server2:8081"
))
```

## Real-Time Monitoring

Poll for value changes:

```python
import asyncio
from basyx_client import AASClient

async def monitor_value(url, submodel_id, element_path, interval=1.0):
    async with AASClient(url) as client:
        last_value = None
        while True:
            try:
                value = await client.submodels.elements.get_value_async(
                    submodel_id, element_path
                )
                if value != last_value:
                    print(f"Value changed: {last_value} -> {value}")
                    last_value = value
            except Exception as e:
                print(f"Error: {e}")

            await asyncio.sleep(interval)

# Run with timeout
async def main():
    try:
        await asyncio.wait_for(
            monitor_value(
                "http://localhost:8081",
                "urn:example:submodel:sensors",
                "Temperature"
            ),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        print("Monitoring stopped")

asyncio.run(main())
```

## Batch Operations

Process large datasets in batches:

```python
import asyncio
from basyx_client import AASClient

async def process_batch(client, submodel_ids):
    tasks = [
        client.submodels.elements.get_value_async(id, "Status")
        for id in submodel_ids
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    async with AASClient("http://localhost:8081") as client:
        result = await client.submodels.list_async()
        all_ids = [sm.id for sm in result.result]

        # Process in batches of 10
        batch_size = 10
        for i in range(0, len(all_ids), batch_size):
            batch = all_ids[i:i + batch_size]
            results = await process_batch(client, batch)

            for id, status in zip(batch, results):
                if isinstance(status, Exception):
                    print(f"{id}: ERROR - {status}")
                else:
                    print(f"{id}: {status}")

asyncio.run(main())
```
