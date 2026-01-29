"""
SwiftAPI Pagination System.

Built-in pagination with limit/offset and cursor-based support.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any, TypeVar
from urllib.parse import urlencode

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest


T = TypeVar("T")


class BasePagination:
    """
    Base class for pagination.

    All pagination classes should inherit from this and implement
    paginate_queryset() and get_paginated_response().
    """

    def paginate_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> list[Any]:
        """
        Paginate the queryset.

        Args:
            queryset: QuerySet to paginate
            request: Current HTTP request

        Returns:
            List of paginated items
        """
        raise NotImplementedError

    def get_paginated_response(self, data: list[Any]) -> dict[str, Any]:
        """
        Build the paginated response.

        Args:
            data: Paginated and serialized data

        Returns:
            Response dictionary with pagination metadata
        """
        raise NotImplementedError


class LimitOffsetPagination(BasePagination):
    """
    Limit/offset pagination.

    Uses query parameters:
    - limit: Maximum number of items to return
    - offset: Starting position

    Example:
        GET /api/users/?limit=10&offset=20

    Response:
        {
            "count": 100,
            "next": "/api/users/?limit=10&offset=30",
            "previous": "/api/users/?limit=10&offset=10",
            "results": [...]
        }
    """

    default_limit = 25
    max_limit = 100
    limit_query_param = "limit"
    offset_query_param = "offset"

    def __init__(
        self,
        default_limit: int | None = None,
        max_limit: int | None = None,
    ) -> None:
        """
        Initialize pagination.

        Args:
            default_limit: Default page size
            max_limit: Maximum allowed page size
        """
        from swiftapi.conf import settings

        if default_limit:
            self.default_limit = default_limit
        else:
            self.default_limit = settings.PAGE_SIZE

        if max_limit:
            self.max_limit = max_limit
        else:
            self.max_limit = settings.MAX_PAGE_SIZE

        self.count: int = 0
        self.limit: int = self.default_limit
        self.offset: int = 0
        self.request: HttpRequest | None = None

    def paginate_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> list[Any]:
        """Paginate queryset with limit/offset."""
        self.request = request

        # Get limit from query params
        self.limit = self._get_limit(request)

        # Get offset from query params
        self.offset = self._get_offset(request)

        # Get total count
        self.count = queryset.count()

        # Apply pagination
        return list(queryset[self.offset : self.offset + self.limit])

    async def apaginate_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> list[Any]:
        """Async version of paginate_queryset."""
        self.request = request
        self.limit = self._get_limit(request)
        self.offset = self._get_offset(request)

        # Async count
        self.count = await queryset.acount()

        # Apply pagination and convert to list
        return [obj async for obj in queryset[self.offset : self.offset + self.limit]]

    def _get_limit(self, request: HttpRequest) -> int:
        """Get limit from request."""
        try:
            limit = int(request.GET.get(self.limit_query_param, self.default_limit))
            return min(limit, self.max_limit)
        except (ValueError, TypeError):
            return self.default_limit

    def _get_offset(self, request: HttpRequest) -> int:
        """Get offset from request."""
        try:
            offset = int(request.GET.get(self.offset_query_param, 0))
            return max(offset, 0)
        except (ValueError, TypeError):
            return 0

    def get_paginated_response(self, data: list[Any]) -> dict[str, Any]:
        """Build paginated response."""
        return {
            "count": self.count,
            "next": self._get_next_link(),
            "previous": self._get_previous_link(),
            "results": data,
        }

    def _get_next_link(self) -> str | None:
        """Get URL for next page."""
        if self.offset + self.limit >= self.count:
            return None

        return self._build_url(self.offset + self.limit)

    def _get_previous_link(self) -> str | None:
        """Get URL for previous page."""
        if self.offset <= 0:
            return None

        previous_offset = max(self.offset - self.limit, 0)
        return self._build_url(previous_offset)

    def _build_url(self, offset: int) -> str:
        """Build URL with pagination params."""
        if self.request is None:
            return ""

        params = dict(self.request.GET)
        params[self.offset_query_param] = [str(offset)]
        params[self.limit_query_param] = [str(self.limit)]

        # Flatten single-item lists
        flat_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        return f"{self.request.path}?{urlencode(flat_params)}"


class PageNumberPagination(BasePagination):
    """
    Page number pagination.

    Uses query parameters:
    - page: Page number (1-indexed)
    - page_size: Number of items per page (optional)

    Example:
        GET /api/users/?page=2&page_size=20
    """

    page_size = 25
    max_page_size = 100
    page_query_param = "page"
    page_size_query_param = "page_size"

    def __init__(
        self,
        page_size: int | None = None,
        max_page_size: int | None = None,
    ) -> None:
        from swiftapi.conf import settings

        self.page_size = page_size or settings.PAGE_SIZE
        self.max_page_size = max_page_size or settings.MAX_PAGE_SIZE

        self.page: int = 1
        self.count: int = 0
        self.request: HttpRequest | None = None

    def paginate_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> list[Any]:
        """Paginate queryset by page number."""
        self.request = request

        # Get page size
        page_size = self._get_page_size(request)

        # Get page number
        self.page = self._get_page(request)

        # Get total count
        self.count = queryset.count()

        # Calculate offset
        offset = (self.page - 1) * page_size

        return list(queryset[offset : offset + page_size])

    def _get_page(self, request: HttpRequest) -> int:
        """Get page number from request."""
        try:
            page = int(request.GET.get(self.page_query_param, 1))
            return max(page, 1)
        except (ValueError, TypeError):
            return 1

    def _get_page_size(self, request: HttpRequest) -> int:
        """Get page size from request."""
        try:
            size = int(
                request.GET.get(self.page_size_query_param, self.page_size)
            )
            return min(size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size

    def get_paginated_response(self, data: list[Any]) -> dict[str, Any]:
        """Build paginated response."""
        page_size = self._get_page_size(self.request) if self.request else self.page_size
        total_pages = (self.count + page_size - 1) // page_size

        return {
            "count": self.count,
            "page": self.page,
            "page_size": page_size,
            "total_pages": total_pages,
            "next": self._get_next_link(total_pages),
            "previous": self._get_previous_link(),
            "results": data,
        }

    def _get_next_link(self, total_pages: int) -> str | None:
        if self.page >= total_pages:
            return None
        return self._build_url(self.page + 1)

    def _get_previous_link(self) -> str | None:
        if self.page <= 1:
            return None
        return self._build_url(self.page - 1)

    def _build_url(self, page: int) -> str:
        if self.request is None:
            return ""

        params = dict(self.request.GET)
        params[self.page_query_param] = [str(page)]
        flat_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        return f"{self.request.path}?{urlencode(flat_params)}"


class CursorPagination(BasePagination):
    """
    Cursor-based pagination for high-performance scenarios.

    Uses an opaque cursor for efficient pagination without offset.
    Better for large datasets and real-time data.

    Uses query parameters:
    - cursor: Opaque cursor string
    - limit: Number of items per page
    """

    cursor_query_param = "cursor"
    page_size = 25
    ordering = "-id"  # Default ordering field

    def __init__(
        self,
        page_size: int | None = None,
        ordering: str | None = None,
    ) -> None:
        from swiftapi.conf import settings

        self.page_size = page_size or settings.PAGE_SIZE
        if ordering:
            self.ordering = ordering

        self.has_next: bool = False
        self.has_previous: bool = False
        self.next_cursor: str | None = None
        self.previous_cursor: str | None = None
        self.request: HttpRequest | None = None

    def paginate_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> list[Any]:
        """Paginate queryset with cursor."""
        self.request = request

        # Apply ordering
        field = self.ordering.lstrip("-")
        descending = self.ordering.startswith("-")
        queryset = queryset.order_by(self.ordering)

        # Decode cursor
        cursor = request.GET.get(self.cursor_query_param)
        cursor_value = self._decode_cursor(cursor) if cursor else None

        # Apply cursor filter
        if cursor_value is not None:
            if descending:
                queryset = queryset.filter(**{f"{field}__lt": cursor_value})
            else:
                queryset = queryset.filter(**{f"{field}__gt": cursor_value})

        # Fetch one extra to check if there's a next page
        results = list(queryset[: self.page_size + 1])

        # Determine if there's a next page
        self.has_next = len(results) > self.page_size
        if self.has_next:
            results = results[: self.page_size]

        # Build cursors
        if results:
            last_item = results[-1]
            self.next_cursor = self._encode_cursor(getattr(last_item, field))

            first_item = results[0]
            self.previous_cursor = self._encode_cursor(getattr(first_item, field))

        self.has_previous = cursor is not None

        return results

    def _encode_cursor(self, value: Any) -> str:
        """Encode cursor value."""
        return base64.urlsafe_b64encode(str(value).encode()).decode()

    def _decode_cursor(self, cursor: str) -> Any:
        """Decode cursor value."""
        try:
            return base64.urlsafe_b64decode(cursor.encode()).decode()
        except Exception:
            return None

    def get_paginated_response(self, data: list[Any]) -> dict[str, Any]:
        """Build paginated response."""
        return {
            "next": self._get_next_link(),
            "previous": self._get_previous_link(),
            "results": data,
        }

    def _get_next_link(self) -> str | None:
        if not self.has_next or not self.next_cursor:
            return None
        return self._build_url(self.next_cursor)

    def _get_previous_link(self) -> str | None:
        if not self.has_previous or not self.previous_cursor:
            return None
        return self._build_url(self.previous_cursor)

    def _build_url(self, cursor: str) -> str:
        if self.request is None:
            return ""

        params = dict(self.request.GET)
        params[self.cursor_query_param] = [cursor]
        flat_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        return f"{self.request.path}?{urlencode(flat_params)}"
