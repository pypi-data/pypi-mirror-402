# Pagination

AAS Part 2 API uses cursor-based pagination for list operations.

## PaginatedResult

All list operations return a `PaginatedResult`:

```python
from basyx_client import AASClient

with AASClient("http://localhost:8081") as client:
    result = client.shells.list()

    # Access items
    for shell in result.result:
        print(shell.id)

    # Check for more pages
    if result.paging_metadata:
        cursor = result.paging_metadata.get("cursor")
        print(f"Next page cursor: {cursor}")
```

## Manual Pagination

Fetch pages manually with cursor:

```python
with AASClient("http://localhost:8081") as client:
    cursor = None
    all_shells = []

    while True:
        result = client.shells.list(limit=50, cursor=cursor)
        all_shells.extend(result.result)

        if not result.paging_metadata or not result.paging_metadata.get("cursor"):
            break
        cursor = result.paging_metadata["cursor"]

    print(f"Total shells: {len(all_shells)}")
```

## iterate_pages Helper

The `iterate_pages` function simplifies fetching all pages:

```python
from basyx_client import AASClient
from basyx_client.pagination import iterate_pages

with AASClient("http://localhost:8081") as client:
    # Iterate through all shells
    for shell in iterate_pages(client.shells.list):
        print(shell.id)

    # With custom limit per page
    for sm in iterate_pages(client.submodels.list, limit=100):
        print(sm.id_short)
```

## Async Pagination

Use `iterate_pages_async` for async iteration:

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

## Filtering with Pagination

Combine filters with pagination:

```python
from basyx_client.pagination import iterate_pages

with AASClient("http://localhost:8081") as client:
    # All submodels with specific semantic ID
    for sm in iterate_pages(
        client.submodels.list,
        semantic_id="https://admin-shell.io/idta/nameplate/2/0"
    ):
        print(sm.id)
```

## Collecting All Results

Convert iterator to list:

```python
# Synchronous
all_shells = list(iterate_pages(client.shells.list))

# Async
async def get_all():
    return [s async for s in iterate_pages_async(client.shells.list_async)]
```

## Performance Considerations

### Limit Per Page

Choose an appropriate limit based on your use case:

```python
# Faster for large datasets (fewer requests)
for sm in iterate_pages(client.submodels.list, limit=1000):
    process(sm)

# Better for memory-constrained environments
for sm in iterate_pages(client.submodels.list, limit=50):
    process(sm)
```

### Concurrent Page Fetching

For very large datasets, fetch pages concurrently:

```python
import asyncio

async def fetch_all_fast():
    async with AASClient("http://localhost:8081") as client:
        # Get first page to determine total
        first = await client.shells.list_async(limit=100)
        all_items = list(first.result)

        cursor = first.paging_metadata.get("cursor") if first.paging_metadata else None
        if not cursor:
            return all_items

        # Fetch remaining pages concurrently (simplified)
        # In practice, you'd need to handle cursor chaining
        return all_items

asyncio.run(fetch_all_fast())
```

## Submodel Elements Pagination

Elements within submodels are also paginated:

```python
with AASClient("http://localhost:8081") as client:
    # Paginate through elements
    for element in iterate_pages(
        lambda **kw: client.submodels.elements.list("urn:sm:1", **kw)
    ):
        print(f"{element.id_short}: {type(element).__name__}")
```
