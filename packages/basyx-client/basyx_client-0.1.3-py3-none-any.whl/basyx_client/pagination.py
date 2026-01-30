"""
Pagination support for AAS Part 2 API.

The API uses cursor-based pagination with:
- `limit`: Number of items per page (max typically 100)
- `cursor`: Opaque cursor string for the next page

This module provides:
- PaginatedResult: Container for a page of results with metadata
- iterate_pages: Convenience function for iterating through all pages
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Iterator

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """
    A page of results from a paginated API endpoint.

    Attributes:
        items: The items in this page
        cursor: Cursor for the next page (None if no more pages)
        has_more: Whether there are more pages available

    Example:
        result = client.shells.list(limit=10)
        for aas in result.items:
            print(aas.id_short)

        if result.has_more:
            next_page = client.shells.list(limit=10, cursor=result.cursor)
    """

    items: list[T]
    cursor: str | None = None
    has_more: bool = False

    def __iter__(self) -> Iterator[T]:
        """Iterate over items in this page."""
        return iter(self.items)

    def __len__(self) -> int:
        """Return the number of items in this page."""
        return len(self.items)


def iterate_pages(
    fetch_func: Callable[[int, str | None], PaginatedResult[T]],
    page_size: int = 100,
) -> Iterator[T]:
    """
    Iterate through all pages of a paginated endpoint.

    This is a convenience function that automatically handles pagination,
    yielding individual items from each page.

    Args:
        fetch_func: Function that takes (limit, cursor) and returns PaginatedResult
        page_size: Number of items to fetch per page (default 100)

    Yields:
        Individual items from all pages

    Example:
        # Iterate through all AAS shells
        for aas in iterate_pages(
            lambda limit, cursor: client.shells.list(limit=limit, cursor=cursor)
        ):
            print(aas.id_short)

        # Or using functools.partial
        from functools import partial
        all_shells = list(iterate_pages(partial(client.shells.list)))
    """
    cursor: str | None = None

    while True:
        result = fetch_func(page_size, cursor)
        yield from result.items

        if not result.has_more or result.cursor is None:
            break

        cursor = result.cursor


async def iterate_pages_async(
    fetch_func: Callable[[int, str | None], Awaitable[PaginatedResult[T]]],
    page_size: int = 100,
) -> AsyncIterator[T]:
    """
    Async version of iterate_pages.

    Args:
        fetch_func: Async function that takes (limit, cursor) and returns PaginatedResult
        page_size: Number of items to fetch per page (default 100)

    Yields:
        Individual items from all pages

    Example:
        async for aas in iterate_pages_async(
            lambda limit, cursor: client.shells.list_async(limit=limit, cursor=cursor)
        ):
            print(aas.id_short)
    """

    cursor: str | None = None

    while True:
        result = await fetch_func(page_size, cursor)
        for item in result.items:
            yield item

        if not result.has_more or result.cursor is None:
            break

        cursor = result.cursor
