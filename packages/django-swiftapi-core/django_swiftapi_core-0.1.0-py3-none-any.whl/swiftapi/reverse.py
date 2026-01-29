"""
SwiftAPI URL Reverse.

URL reversing utilities with request context - similar to DRF's reverse.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse as django_reverse

if TYPE_CHECKING:
    from django.http import HttpRequest


def reverse(
    viewname: str,
    args: tuple | list | None = None,
    kwargs: dict | None = None,
    request: HttpRequest | None = None,
    format: str | None = None,
) -> str:
    """
    Reverse URL with optional request context for absolute URLs.

    Example:
        from swiftapi.reverse import reverse

        # Relative URL
        url = reverse("user-detail", kwargs={"pk": 1})
        # Returns: "/api/users/1/"

        # Absolute URL with request
        url = reverse("user-detail", kwargs={"pk": 1}, request=request)
        # Returns: "https://example.com/api/users/1/"
    """
    url = django_reverse(viewname, args=args, kwargs=kwargs)

    if format is not None:
        # Add format suffix
        url = replace_query_param(url, "format", format)

    if request is not None:
        url = request.build_absolute_uri(url)

    return url


def reverse_lazy(
    viewname: str,
    args: tuple | list | None = None,
    kwargs: dict | None = None,
    request: HttpRequest | None = None,
    format: str | None = None,
) -> str:
    """
    Lazy version of reverse for use in class attributes.
    """
    from django.utils.functional import lazy
    return lazy(reverse, str)(viewname, args, kwargs, request, format)


def replace_query_param(url: str, key: str, value: str) -> str:
    """
    Replace a query parameter in a URL.

    Example:
        replace_query_param("/api/users/?page=1", "page", "2")
        # Returns: "/api/users/?page=2"
    """
    from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

    parsed = urlparse(url)
    query_dict = parse_qs(parsed.query, keep_blank_values=True)
    query_dict[key] = [value]

    new_query = urlencode(query_dict, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))


def remove_query_param(url: str, key: str) -> str:
    """
    Remove a query parameter from a URL.

    Example:
        remove_query_param("/api/users/?page=1&search=test", "page")
        # Returns: "/api/users/?search=test"
    """
    from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

    parsed = urlparse(url)
    query_dict = parse_qs(parsed.query, keep_blank_values=True)
    query_dict.pop(key, None)

    new_query = urlencode(query_dict, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "remove_query_param",
    "replace_query_param",
    "reverse",
    "reverse_lazy",
]
