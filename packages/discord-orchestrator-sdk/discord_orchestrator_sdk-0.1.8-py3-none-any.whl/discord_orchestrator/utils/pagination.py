"""Pagination utilities for the SDK.

Provides helpers for working with paginated API responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterator, Optional, TypeVar

from ..constants import DEFAULT_PAGE_LIMIT, DEFAULT_OFFSET

T = TypeVar("T")


@dataclass
class PaginationParams:
    """Parameters for paginated requests.

    Attributes:
        limit: Number of items per page
        offset: Starting offset
        max_limit: Optional maximum limit to enforce
    """

    limit: int = DEFAULT_PAGE_LIMIT
    offset: int = DEFAULT_OFFSET
    max_limit: Optional[int] = None

    def to_dict(self) -> dict[str, int]:
        """Convert to dict for API requests.

        Returns:
            Dict with limit and offset keys
        """
        limit = self.limit
        if self.max_limit is not None:
            limit = min(limit, self.max_limit)
        return {"limit": limit, "offset": self.offset}

    def next_page(self, items_received: int) -> "PaginationParams":
        """Get parameters for the next page.

        Args:
            items_received: Number of items received in current page

        Returns:
            New PaginationParams for the next page
        """
        return PaginationParams(
            limit=self.limit,
            offset=self.offset + items_received,
            max_limit=self.max_limit,
        )


class Paginator(Generic[T]):
    """Iterator for paginated API results.

    Automatically handles pagination by fetching pages as needed.

    Example:
        >>> def fetch_bots(limit: int, offset: int) -> list[dict]:
        ...     return client._http.get("/bots", params={"limit": limit, "offset": offset})
        >>>
        >>> paginator = Paginator(fetch_bots, page_size=50)
        >>> for bot in paginator:
        ...     print(bot["name"])
    """

    def __init__(
        self,
        fetch_fn: Callable[[int, int], list[T]],
        page_size: int = DEFAULT_PAGE_LIMIT,
        max_items: Optional[int] = None,
    ):
        """Initialize the paginator.

        Args:
            fetch_fn: Function that fetches a page, takes (limit, offset) and returns list
            page_size: Number of items to fetch per page
            max_items: Maximum total items to return (None for unlimited)
        """
        self.fetch_fn = fetch_fn
        self.page_size = page_size
        self.max_items = max_items

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items across pages.

        Yields:
            Items from each page
        """
        offset = 0
        total_yielded = 0

        while True:
            # Respect max_items limit
            limit = self.page_size
            if self.max_items is not None:
                remaining = self.max_items - total_yielded
                if remaining <= 0:
                    break
                limit = min(limit, remaining)

            items = self.fetch_fn(limit, offset)
            if not items:
                break

            for item in items:
                yield item
                total_yielded += 1

                if self.max_items is not None and total_yielded >= self.max_items:
                    return

            # If we got fewer items than requested, we've reached the end
            if len(items) < limit:
                break

            offset += len(items)

    def pages(self) -> Iterator[list[T]]:
        """Iterate over pages instead of individual items.

        Yields:
            List of items for each page
        """
        offset = 0
        total_yielded = 0

        while True:
            limit = self.page_size
            if self.max_items is not None:
                remaining = self.max_items - total_yielded
                if remaining <= 0:
                    break
                limit = min(limit, remaining)

            items = self.fetch_fn(limit, offset)
            if not items:
                break

            yield items
            total_yielded += len(items)

            if len(items) < limit:
                break

            offset += len(items)

    def collect(self) -> list[T]:
        """Fetch all items and return as a list.

        Returns:
            List of all items
        """
        return list(self)


def paginate_results(
    fetch_fn: Callable[[int, int], list[T]],
    page_size: int = DEFAULT_PAGE_LIMIT,
    max_items: Optional[int] = None,
) -> list[T]:
    """Convenience function to fetch all paginated results.

    Args:
        fetch_fn: Function that fetches a page, takes (limit, offset)
        page_size: Number of items per page
        max_items: Maximum total items to return

    Returns:
        List of all items

    Example:
        >>> all_bots = paginate_results(
        ...     lambda limit, offset: client._http.get("/bots", params={"limit": limit, "offset": offset}),
        ...     page_size=100
        ... )
    """
    return Paginator(fetch_fn, page_size, max_items).collect()
