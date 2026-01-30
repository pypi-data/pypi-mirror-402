#!/usr/bin/env python3
"""Handling large datasets with pagination.

This example demonstrates:
- Manual pagination with cursors
- Using iterate_pages helper
- Processing large datasets efficiently
- Memory-efficient streaming

Prerequisites:
    pip install basyx-client
    # Start BaSyx server on localhost:8081
"""

from basyx_client import AASClient
from basyx_client.pagination import iterate_pages

BASE_URL = "http://localhost:8081"


def manual_pagination() -> None:
    """Manually paginate through results."""
    print("1. Manual pagination...")

    with AASClient(BASE_URL) as client:
        all_shells = []
        cursor = None
        page = 0

        while True:
            page += 1
            result = client.shells.list(limit=10, cursor=cursor)
            all_shells.extend(result.result)
            print(f"   Page {page}: {len(result.result)} items")

            # Check for more pages
            if not result.paging_metadata:
                break
            cursor = result.paging_metadata.get("cursor")
            if not cursor:
                break

        print(f"   Total: {len(all_shells)} shells")


def using_iterate_pages() -> None:
    """Use iterate_pages helper for automatic pagination."""
    print("\n2. Using iterate_pages helper...")

    with AASClient(BASE_URL) as client:
        count = 0
        for shell in iterate_pages(client.shells.list, limit=10):
            count += 1
            if count <= 5:
                print(f"   {count}. {shell.id_short}")
            elif count == 6:
                print("   ...")

        print(f"   Total: {count} shells")


def collect_all_to_list() -> None:
    """Collect all items into a list."""
    print("\n3. Collecting all to list...")

    with AASClient(BASE_URL) as client:
        all_submodels = list(iterate_pages(client.submodels.list, limit=50))
        print(f"   Collected {len(all_submodels)} submodels")

        # Group by semantic ID
        semantic_groups: dict[str, int] = {}
        for sm in all_submodels:
            sem_id = "none"
            if hasattr(sm, "semantic_id") and sm.semantic_id:
                keys = getattr(sm.semantic_id, "key", [])
                if keys:
                    sem_id = str(getattr(keys[0], "value", "unknown"))[:40]
            semantic_groups[sem_id] = semantic_groups.get(sem_id, 0) + 1

        print("   Submodels by semantic ID:")
        for sem_id, count in sorted(
            semantic_groups.items(), key=lambda x: -x[1]
        )[:5]:
            print(f"      {sem_id}: {count}")


def streaming_processing() -> None:
    """Process items as they stream (memory efficient)."""
    print("\n4. Streaming processing...")

    with AASClient(BASE_URL) as client:
        total_elements = 0
        sm_count = 0

        # Process each submodel without loading all into memory
        for sm in iterate_pages(client.submodels.list, limit=20):
            sm_count += 1
            elements = sm.submodel_element or []
            total_elements += len(elements)

        print(f"   Processed {sm_count} submodels")
        print(f"   Total elements: {total_elements}")
        avg = total_elements / sm_count if sm_count else 0
        print(f"   Average elements per submodel: {avg:.1f}")


def filtered_pagination() -> None:
    """Combine filters with pagination."""
    print("\n5. Filtered pagination...")

    with AASClient(BASE_URL) as client:
        # Filter by semantic ID (if supported by server)
        count = 0
        for sm in iterate_pages(
            client.submodels.list,
            limit=10,
            # semantic_id="https://admin-shell.io/idta/nameplate/2/0",
        ):
            count += 1
            print(f"   - {sm.id_short}")
            if count >= 5:
                print("   ... (truncated)")
                break

        print(f"   Shown: {min(count, 5)} of {count}")


def pagination_stats() -> None:
    """Gather statistics from paginated data."""
    print("\n6. Pagination statistics...")

    with AASClient(BASE_URL) as client:
        # Count different model types
        type_counts: dict[str, int] = {}

        for sm in iterate_pages(client.submodels.list, limit=50):
            for elem in sm.submodel_element or []:
                type_name = type(elem).__name__
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

        print("   Element types across all submodels:")
        for type_name, count in sorted(
            type_counts.items(), key=lambda x: -x[1]
        )[:10]:
            print(f"      {type_name}: {count}")


def main() -> None:
    """Run pagination examples."""
    print("=== basyx-client Pagination Examples ===\n")

    manual_pagination()
    using_iterate_pages()
    collect_all_to_list()
    streaming_processing()
    filtered_pagination()
    pagination_stats()

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
