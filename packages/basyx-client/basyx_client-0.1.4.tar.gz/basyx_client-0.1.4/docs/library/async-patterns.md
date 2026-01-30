# Async Patterns

basyx-client provides full async support for high-performance applications.

## Basic Async Usage

```python
import asyncio
from basyx_client import AASClient

async def main():
    async with AASClient("http://localhost:8081") as client:
        result = await client.shells.list_async()
        for shell in result.result:
            print(shell.id)

asyncio.run(main())
```

## Concurrent Requests

Fetch multiple resources simultaneously:

```python
import asyncio
from basyx_client import AASClient

async def main():
    async with AASClient("http://localhost:8081") as client:
        # Get list of submodel IDs
        result = await client.submodels.list_async()
        ids = [sm.id for sm in result.result]

        # Fetch all submodels concurrently
        tasks = [client.submodels.get_async(id) for id in ids]
        submodels = await asyncio.gather(*tasks)

        for sm in submodels:
            print(f"{sm.id_short}: {len(sm.submodel_element or [])} elements")

asyncio.run(main())
```

## Semaphore for Rate Limiting

Control concurrent request rate:

```python
import asyncio
from basyx_client import AASClient

async def fetch_with_limit(client, semaphore, submodel_id):
    async with semaphore:
        return await client.submodels.get_async(submodel_id)

async def main():
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

    async with AASClient("http://localhost:8081") as client:
        result = await client.submodels.list_async()
        ids = [sm.id for sm in result.result]

        tasks = [fetch_with_limit(client, semaphore, id) for id in ids]
        submodels = await asyncio.gather(*tasks)

asyncio.run(main())
```

## Async Pagination

Iterate through pages asynchronously:

```python
import asyncio
from basyx_client import AASClient
from basyx_client.pagination import iterate_pages_async

async def main():
    async with AASClient("http://localhost:8081") as client:
        async for shell in iterate_pages_async(client.shells.list_async):
            print(shell.id)

asyncio.run(main())
```

## Error Handling in Async

```python
import asyncio
from basyx_client import AASClient, ResourceNotFoundError

async def safe_get(client, aas_id):
    try:
        return await client.shells.get_async(aas_id)
    except ResourceNotFoundError:
        return None

async def main():
    async with AASClient("http://localhost:8081") as client:
        ids = ["urn:aas:1", "urn:aas:2", "nonexistent"]
        tasks = [safe_get(client, id) for id in ids]
        results = await asyncio.gather(*tasks)

        for id, result in zip(ids, results):
            if result:
                print(f"Found: {id}")
            else:
                print(f"Not found: {id}")

asyncio.run(main())
```

## Async Context Patterns

### Multiple Clients

```python
async def compare_servers():
    async with AASClient("http://server1:8081") as c1, \
               AASClient("http://server2:8081") as c2:

        shells1, shells2 = await asyncio.gather(
            c1.shells.list_async(),
            c2.shells.list_async()
        )

        ids1 = {s.id for s in shells1.result}
        ids2 = {s.id for s in shells2.result}

        print(f"Only on server1: {ids1 - ids2}")
        print(f"Only on server2: {ids2 - ids1}")
```

### Timeout Handling

```python
async def with_timeout():
    async with AASClient("http://localhost:8081", timeout=5.0) as client:
        try:
            result = await asyncio.wait_for(
                client.shells.list_async(),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            print("Request timed out")
```

## Integration with Web Frameworks

### FastAPI

```python
from fastapi import FastAPI, Depends
from basyx_client import AASClient

app = FastAPI()
client = AASClient("http://localhost:8081")

@app.on_event("startup")
async def startup():
    await client.__aenter__()

@app.on_event("shutdown")
async def shutdown():
    await client.__aexit__(None, None, None)

@app.get("/shells")
async def list_shells():
    result = await client.shells.list_async()
    return [{"id": s.id, "idShort": s.id_short} for s in result.result]
```

### aiohttp

```python
from aiohttp import web
from basyx_client import AASClient

async def list_shells(request):
    async with AASClient("http://localhost:8081") as client:
        result = await client.shells.list_async()
        return web.json_response([s.id for s in result.result])

app = web.Application()
app.router.add_get("/shells", list_shells)
```
