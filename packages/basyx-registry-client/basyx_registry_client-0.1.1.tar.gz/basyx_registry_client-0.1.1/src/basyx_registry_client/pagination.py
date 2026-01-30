# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Pagination utilities for AAS Registry API responses.

The AAS Registry API uses cursor-based pagination for list endpoints.
This module provides a generic container for paginated responses that
works with any item type.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PagedResult(BaseModel, Generic[T]):
    """Container for paginated API responses.

    A generic container that holds a page of items from a list endpoint,
    along with a cursor for fetching the next page.

    This class is a Pydantic model, enabling JSON serialization and
    validation of paginated responses.

    Attributes:
        items: List of items in this page.
        cursor: Cursor for fetching the next page, or None if this is
            the last page.

    Type Parameters:
        T: The type of items in the page.

    Examples:
        >>> from basyx_registry_client.pagination import PagedResult
        >>> page: PagedResult[str] = PagedResult(items=["a", "b", "c"], cursor="next123")
        >>> len(page)
        3
        >>> list(page)
        ['a', 'b', 'c']
        >>> page.has_more
        True
    """

    model_config = ConfigDict(frozen=True)

    items: list[T]
    cursor: str | None = None

    def __iter__(self) -> Iterator[T]:  # type: ignore[override]
        """Iterate over items in this page.

        Yields:
            Each item in the page.
        """
        return iter(self.items)

    def __len__(self) -> int:
        """Return the number of items in this page.

        Returns:
            The count of items in this page.
        """
        return len(self.items)

    @property
    def has_more(self) -> bool:
        """Check if there are more pages available.

        Returns:
            True if there is a cursor indicating more pages, False otherwise.
        """
        return self.cursor is not None

    def __bool__(self) -> bool:
        """Check if the page contains any items.

        Returns:
            True if there is at least one item, False if empty.
        """
        return len(self.items) > 0
