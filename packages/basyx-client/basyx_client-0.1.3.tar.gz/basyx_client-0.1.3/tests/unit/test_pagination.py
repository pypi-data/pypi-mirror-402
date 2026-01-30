"""Unit tests for pagination utilities."""

from basyx_client.pagination import PaginatedResult, iterate_pages


class TestPaginatedResult:
    """Tests for PaginatedResult class."""

    def test_empty_result(self) -> None:
        """Test empty paginated result."""
        result: PaginatedResult[str] = PaginatedResult(items=[])

        assert len(result) == 0
        assert list(result) == []
        assert result.cursor is None
        assert result.has_more is False

    def test_result_with_items(self) -> None:
        """Test paginated result with items."""
        items = ["item1", "item2", "item3"]
        result: PaginatedResult[str] = PaginatedResult(items=items)

        assert len(result) == 3
        assert list(result) == items

    def test_result_with_pagination_metadata(self) -> None:
        """Test paginated result with cursor."""
        result: PaginatedResult[str] = PaginatedResult(
            items=["item1", "item2"],
            cursor="next-page-cursor",
            has_more=True,
        )

        assert result.cursor == "next-page-cursor"
        assert result.has_more is True

    def test_iteration(self) -> None:
        """Test that result is iterable."""
        items = [1, 2, 3, 4, 5]
        result: PaginatedResult[int] = PaginatedResult(items=items)

        # Test direct iteration
        collected = []
        for item in result:
            collected.append(item)
        assert collected == items

    def test_len(self) -> None:
        """Test len() on result."""
        result: PaginatedResult[str] = PaginatedResult(items=["a", "b", "c"])
        assert len(result) == 3


class TestIteratePages:
    """Tests for iterate_pages function."""

    def test_single_page(self) -> None:
        """Test iterating through a single page."""

        # Mock fetch function that returns one page
        def fetch(limit: int, cursor: str | None) -> PaginatedResult[str]:
            return PaginatedResult(items=["a", "b", "c"], has_more=False)

        items = list(iterate_pages(fetch))
        assert items == ["a", "b", "c"]

    def test_multiple_pages(self) -> None:
        """Test iterating through multiple pages."""
        call_count = 0

        def fetch(limit: int, cursor: str | None) -> PaginatedResult[str]:
            nonlocal call_count
            call_count += 1

            if cursor is None:
                # First page
                return PaginatedResult(
                    items=["a", "b"],
                    cursor="page2",
                    has_more=True,
                )
            elif cursor == "page2":
                # Second page
                return PaginatedResult(
                    items=["c", "d"],
                    cursor="page3",
                    has_more=True,
                )
            else:
                # Last page
                return PaginatedResult(
                    items=["e"],
                    has_more=False,
                )

        items = list(iterate_pages(fetch))

        assert items == ["a", "b", "c", "d", "e"]
        assert call_count == 3

    def test_empty_result(self) -> None:
        """Test iterating through empty result."""

        def fetch(limit: int, cursor: str | None) -> PaginatedResult[str]:
            return PaginatedResult(items=[], has_more=False)

        items = list(iterate_pages(fetch))
        assert items == []

    def test_custom_page_size(self) -> None:
        """Test that page size is passed to fetch function."""
        captured_limits = []

        def fetch(limit: int, cursor: str | None) -> PaginatedResult[str]:
            captured_limits.append(limit)
            return PaginatedResult(items=["a"], has_more=False)

        list(iterate_pages(fetch, page_size=50))

        assert captured_limits == [50]

    def test_cursor_passed_correctly(self) -> None:
        """Test that cursor is passed correctly between pages."""
        captured_cursors = []

        def fetch(limit: int, cursor: str | None) -> PaginatedResult[str]:
            captured_cursors.append(cursor)
            if cursor is None:
                return PaginatedResult(items=["a"], cursor="cursor1", has_more=True)
            elif cursor == "cursor1":
                return PaginatedResult(items=["b"], cursor="cursor2", has_more=True)
            else:
                return PaginatedResult(items=["c"], has_more=False)

        list(iterate_pages(fetch))

        assert captured_cursors == [None, "cursor1", "cursor2"]

    def test_stops_on_none_cursor(self) -> None:
        """Test that iteration stops when cursor becomes None."""
        call_count = 0

        def fetch(limit: int, cursor: str | None) -> PaginatedResult[str]:
            nonlocal call_count
            call_count += 1
            # Returns has_more=True but cursor=None (inconsistent but should handle)
            return PaginatedResult(items=["a"], cursor=None, has_more=True)

        items = list(iterate_pages(fetch))

        assert items == ["a"]
        assert call_count == 1

    def test_generator_behavior(self) -> None:
        """Test that iterate_pages returns a generator (lazy evaluation)."""
        call_count = 0

        def fetch(limit: int, cursor: str | None) -> PaginatedResult[str]:
            nonlocal call_count
            call_count += 1
            if cursor is None:
                return PaginatedResult(items=["a", "b"], cursor="page2", has_more=True)
            return PaginatedResult(items=["c"], has_more=False)

        # Create generator but don't consume it
        gen = iterate_pages(fetch)

        # No calls yet (lazy)
        assert call_count == 0

        # Consume first item
        next(gen)
        assert call_count == 1

        # Consume second item (same page)
        next(gen)
        assert call_count == 1

        # Consume third item (triggers next page fetch)
        next(gen)
        assert call_count == 2


class TestPaginatedResultGenericType:
    """Test PaginatedResult with different generic types."""

    def test_with_dict_items(self) -> None:
        """Test with dict items."""
        items = [{"id": 1}, {"id": 2}]
        result: PaginatedResult[dict] = PaginatedResult(items=items)

        assert list(result) == items

    def test_with_custom_class(self) -> None:
        """Test with custom class items."""

        class Item:
            def __init__(self, name: str) -> None:
                self.name = name

        items = [Item("a"), Item("b")]
        result: PaginatedResult[Item] = PaginatedResult(items=items)

        names = [item.name for item in result]
        assert names == ["a", "b"]
