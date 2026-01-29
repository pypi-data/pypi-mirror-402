"""
SwiftAPI Filtering and Ordering System.

Query parameter based filtering and ordering for list endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models import Q

from swiftapi.exceptions import ValidationError

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest


class BaseFilter:
    """
    Base class for filters.

    Filters modify querysets based on request parameters.
    """

    def filter_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> QuerySet:
        """
        Apply filter to queryset.

        Args:
            queryset: QuerySet to filter
            request: Current HTTP request

        Returns:
            Filtered QuerySet
        """
        raise NotImplementedError


class QueryFilter(BaseFilter):
    """
    Filter queryset by query parameters.

    Supports basic field filtering via query params:
    - ?field=value -> exact match
    - ?field__in=val1,val2 -> in list
    - ?field__gte=value -> greater than or equal
    - ?field__lte=value -> less than or equal
    - ?field__contains=value -> contains (case-sensitive)
    - ?field__icontains=value -> contains (case-insensitive)

    Usage:
        class ArticleViewSet(ViewSet):
            filter_class = QueryFilter
            filter_fields = ["status", "category", "author"]

        # GET /api/articles/?status=published&category=tech
    """

    # Allowed filter suffixes
    FILTER_OPERATORS = {
        "exact": "",
        "in": "__in",
        "gt": "__gt",
        "gte": "__gte",
        "lt": "__lt",
        "lte": "__lte",
        "contains": "__contains",
        "icontains": "__icontains",
        "startswith": "__startswith",
        "istartswith": "__istartswith",
        "endswith": "__endswith",
        "iendswith": "__iendswith",
        "isnull": "__isnull",
        "range": "__range",
    }

    def __init__(
        self,
        fields: list[str] | None = None,
        allow_all: bool = False,
    ) -> None:
        """
        Initialize filter.

        Args:
            fields: Allowed filter fields
            allow_all: If True, allow filtering on any field
        """
        self.fields = fields or []
        self.allow_all = allow_all

    def filter_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> QuerySet:
        """Apply query parameter filters."""
        for key, value in request.GET.items():
            # Skip pagination and ordering params
            if key in ("limit", "offset", "page", "page_size", "cursor", "ordering", "search"):
                continue

            # Parse field and operator
            field, operator = self._parse_filter_key(key)

            if field is None:
                continue

            # Check if field is allowed
            if not self.allow_all and field not in self.fields:
                continue

            # Build filter
            filter_kwargs = self._build_filter(field, operator, value)

            if filter_kwargs:
                queryset = queryset.filter(**filter_kwargs)

        return queryset

    def _parse_filter_key(self, key: str) -> tuple[str | None, str]:
        """Parse filter key into field and operator."""
        for operator, suffix in self.FILTER_OPERATORS.items():
            if suffix and key.endswith(suffix):
                field = key[: -len(suffix)]
                return field, operator

        # No operator suffix, use exact match
        return key, "exact"

    def _build_filter(self, field: str, operator: str, value: str) -> dict[str, Any]:
        """Build filter kwargs."""
        suffix = self.FILTER_OPERATORS.get(operator, "")
        filter_key = f"{field}{suffix}"

        # Handle special operators
        if operator == "in":
            value = value.split(",")  # type: ignore
        elif operator == "isnull":
            value = value.lower() in ("true", "1", "yes")  # type: ignore
        elif operator == "range":
            parts = value.split(",")
            if len(parts) == 2:
                value = parts  # type: ignore
            else:
                return {}

        return {filter_key: value}


class OrderingFilter(BaseFilter):
    """
    Order queryset by query parameters.

    Uses ?ordering= query parameter:
    - ?ordering=field -> ascending
    - ?ordering=-field -> descending
    - ?ordering=field1,-field2 -> multiple fields

    Usage:
        class ArticleViewSet(ViewSet):
            ordering_fields = ["created_at", "title", "views"]
            default_ordering = "-created_at"
    """

    ordering_param = "ordering"

    def __init__(
        self,
        fields: list[str] | None = None,
        default: str | None = None,
    ) -> None:
        """
        Initialize ordering filter.

        Args:
            fields: Allowed ordering fields
            default: Default ordering
        """
        self.fields = fields or []
        self.default = default

    def filter_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> QuerySet:
        """Apply ordering to queryset."""
        ordering_param = request.GET.get(self.ordering_param)

        if ordering_param:
            ordering = self._parse_ordering(ordering_param)
        elif self.default:
            ordering = self._parse_ordering(self.default)
        else:
            ordering = None

        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset

    def _parse_ordering(self, ordering_str: str) -> list[str]:
        """Parse ordering string into list of fields."""
        ordering = []

        for field in ordering_str.split(","):
            field = field.strip()

            if not field:
                continue

            # Check if descending
            descending = field.startswith("-")
            field_name = field.lstrip("-")

            # Validate field
            if self.fields and field_name not in self.fields:
                raise ValidationError(
                    f"Invalid ordering field: {field_name}. "
                    f"Allowed fields: {', '.join(self.fields)}"
                )

            ordering.append(f"-{field_name}" if descending else field_name)

        return ordering


class SearchFilter(BaseFilter):
    """
    Full-text search filter.

    Uses ?search= query parameter for searching across multiple fields.

    Usage:
        class ArticleViewSet(ViewSet):
            search_fields = ["title", "content", "author__name"]
    """

    search_param = "search"

    def __init__(
        self,
        fields: list[str] | None = None,
    ) -> None:
        """
        Initialize search filter.

        Args:
            fields: Fields to search in
        """
        self.fields = fields or []

    def filter_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> QuerySet:
        """Apply search filter to queryset."""
        search_term = request.GET.get(self.search_param, "").strip()

        if not search_term or not self.fields:
            return queryset

        # Build OR query across all search fields
        q = Q()
        for field in self.fields:
            q |= Q(**{f"{field}__icontains": search_term})

        return queryset.filter(q)


class FilterSet:
    """
    Combine multiple filters.

    Usage:
        class ArticleViewSet(ViewSet):
            filterset = FilterSet(
                QueryFilter(fields=["status", "category"]),
                SearchFilter(fields=["title", "content"]),
                OrderingFilter(
                    fields=["created_at", "title"],
                    default="-created_at",
                ),
            )
    """

    def __init__(self, *filters: BaseFilter) -> None:
        """
        Initialize filterset.

        Args:
            *filters: Filter instances to apply
        """
        self.filters = filters

    def filter_queryset(
        self,
        queryset: QuerySet,
        request: HttpRequest,
    ) -> QuerySet:
        """Apply all filters to queryset."""
        for filter_instance in self.filters:
            queryset = filter_instance.filter_queryset(queryset, request)

        return queryset


def apply_filters(
    queryset: QuerySet,
    request: HttpRequest,
    filter_fields: list[str] | None = None,
    ordering_fields: list[str] | None = None,
    search_fields: list[str] | None = None,
    default_ordering: str | None = None,
) -> QuerySet:
    """
    Convenience function to apply common filters.

    Args:
        queryset: QuerySet to filter
        request: HTTP request
        filter_fields: Fields allowed for filtering
        ordering_fields: Fields allowed for ordering
        search_fields: Fields for search
        default_ordering: Default ordering

    Returns:
        Filtered queryset
    """
    # Apply query filters
    if filter_fields:
        query_filter = QueryFilter(fields=filter_fields)
        queryset = query_filter.filter_queryset(queryset, request)

    # Apply search
    if search_fields:
        search_filter = SearchFilter(fields=search_fields)
        queryset = search_filter.filter_queryset(queryset, request)

    # Apply ordering
    if ordering_fields or default_ordering:
        ordering_filter = OrderingFilter(
            fields=ordering_fields or [],
            default=default_ordering,
        )
        queryset = ordering_filter.filter_queryset(queryset, request)

    return queryset
