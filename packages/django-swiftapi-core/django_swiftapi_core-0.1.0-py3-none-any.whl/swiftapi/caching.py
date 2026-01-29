"""
SwiftAPI Caching System.

Built-in response caching with cache invalidation support.
"""

from __future__ import annotations

import contextlib
import functools
import hashlib
import time
from typing import TYPE_CHECKING, Any

from django.http import HttpRequest, JsonResponse

if TYPE_CHECKING:
    from collections.abc import Callable

    from swiftapi.viewsets import ViewSet


class CacheBackend:
    """
    Base class for cache backends.
    """

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL."""
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        raise NotImplementedError

    def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        raise NotImplementedError


class DjangoCacheBackend(CacheBackend):
    """
    Cache backend using Django's cache framework.
    """

    def __init__(self, cache_alias: str = "default") -> None:
        from django.core.cache import caches
        self.cache = caches[cache_alias]

    def get(self, key: str) -> Any | None:
        return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: int) -> None:
        self.cache.set(key, value, ttl)

    def delete(self, key: str) -> None:
        self.cache.delete(key)

    def delete_pattern(self, pattern: str) -> None:
        # Django's default cache doesn't support pattern deletion
        # This works with redis-py and similar backends
        with contextlib.suppress(AttributeError):
            self.cache.delete_pattern(pattern)


class InMemoryCacheBackend(CacheBackend):
    """
    Simple in-memory cache for development/testing.
    """

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            value, expires = self._cache[key]
            if expires > time.time():
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._cache[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def delete_pattern(self, pattern: str) -> None:
        import fnmatch
        keys_to_delete = [
            k for k in self._cache
            if fnmatch.fnmatch(k, pattern)
        ]
        for key in keys_to_delete:
            del self._cache[key]


class ResponseCache:
    """
    Response caching for ViewSet actions.

    Usage:
        class ArticleViewSet(ViewSet):
            cache = ResponseCache(ttl=300)  # 5 minutes

            @cache
            async def list(self, request):
                ...
    """

    def __init__(
        self,
        ttl: int = 300,
        key_prefix: str = "swiftapi",
        backend: CacheBackend | None = None,
        vary_on: list[str] | None = None,
    ) -> None:
        """
        Initialize response cache.

        Args:
            ttl: Time to live in seconds
            key_prefix: Prefix for cache keys
            backend: Cache backend (default: DjangoCacheBackend)
            vary_on: Headers to vary cache on
        """
        from swiftapi.conf import settings

        self.ttl = ttl or settings.DEFAULT_CACHE_TTL
        self.key_prefix = key_prefix
        self.backend = backend or DjangoCacheBackend(settings.DEFAULT_CACHE_BACKEND)
        self.vary_on = vary_on or []

    def __call__(self, func: Callable) -> Callable:
        """Decorator to cache a ViewSet method."""

        @functools.wraps(func)
        async def wrapper(viewset: ViewSet, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            # Only cache GET requests
            if request.method != "GET":
                return await func(viewset, request, *args, **kwargs)

            # Generate cache key
            cache_key = self._build_key(request, viewset, args, kwargs)

            # Try to get from cache
            cached = self.backend.get(cache_key)
            if cached is not None:
                return cached

            # Call the actual method
            result = await func(viewset, request, *args, **kwargs)

            # Store in cache
            self.backend.set(cache_key, result, self.ttl)

            return result

        return wrapper

    def _build_key(
        self,
        request: HttpRequest,
        viewset: ViewSet,
        args: tuple,
        kwargs: dict,
    ) -> str:
        """Build a unique cache key for the request."""
        parts = [
            self.key_prefix,
            viewset.__class__.__name__,
            request.path,
            request.META.get("QUERY_STRING", ""),
        ]

        # Add vary headers
        for header in self.vary_on:
            header_key = f"HTTP_{header.upper().replace('-', '_')}"
            parts.append(request.META.get(header_key, ""))

        # Add kwargs (like pk)
        for key, value in sorted(kwargs.items()):
            parts.append(f"{key}:{value}")

        # Hash the parts
        key_string = "|".join(parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"{self.key_prefix}:{key_hash}"

    def invalidate(
        self,
        viewset_class: type | None = None,
        path_pattern: str | None = None,
    ) -> None:
        """
        Invalidate cached responses.

        Args:
            viewset_class: Invalidate all cache for this ViewSet
            path_pattern: Invalidate cache matching path pattern
        """
        if viewset_class:
            pattern = f"{self.key_prefix}:{viewset_class.__name__}:*"
            self.backend.delete_pattern(pattern)

        if path_pattern:
            pattern = f"{self.key_prefix}:*{path_pattern}*"
            self.backend.delete_pattern(pattern)


def cache_response(
    ttl: int = 300,
    key_func: Callable[[HttpRequest], str] | None = None,
    vary_on: list[str] | None = None,
) -> Callable:
    """
    Decorator to cache ViewSet method responses.

    Args:
        ttl: Cache TTL in seconds
        key_func: Custom function to generate cache key
        vary_on: Headers to vary cache on

    Usage:
        class ArticleViewSet(ViewSet):
            @cache_response(ttl=600)
            async def list(self, request):
                ...
    """
    cache = ResponseCache(ttl=ttl, vary_on=vary_on)
    return cache


class ETagMixin:
    """
    Mixin for ViewSets to support ETag-based conditional requests.

    Usage:
        class ArticleViewSet(ETagMixin, ViewSet):
            ...
    """

    def get_etag(self, data: Any) -> str:
        """
        Generate ETag for response data.

        Override to customize ETag generation.
        """
        import json
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()

    async def check_etag(
        self,
        request: HttpRequest,
        data: Any,
    ) -> JsonResponse | None:
        """
        Check If-None-Match header against data ETag.

        Returns 304 Not Modified if ETags match.
        """
        etag = self.get_etag(data)

        if_none_match = request.META.get("HTTP_IF_NONE_MATCH", "")

        if if_none_match and if_none_match.strip('"') == etag:
            response = JsonResponse({}, status=304)
            response["ETag"] = f'"{etag}"'
            return response

        return None

    def add_etag_header(self, response: JsonResponse, data: Any) -> JsonResponse:
        """Add ETag header to response."""
        etag = self.get_etag(data)
        response["ETag"] = f'"{etag}"'
        return response


class LastModifiedMixin:
    """
    Mixin for ViewSets to support Last-Modified conditional requests.
    """

    last_modified_field = "updated_at"

    def get_last_modified(self, obj: Any) -> str | None:
        """Get Last-Modified value from object."""
        value = getattr(obj, self.last_modified_field, None)

        if value is None:
            return None

        if hasattr(value, "strftime"):
            return value.strftime("%a, %d %b %Y %H:%M:%S GMT")

        return str(value)

    async def check_modified_since(
        self,
        request: HttpRequest,
        obj: Any,
    ) -> JsonResponse | None:
        """
        Check If-Modified-Since header.

        Returns 304 Not Modified if not modified since.
        """
        from datetime import datetime

        last_modified = self.get_last_modified(obj)
        if not last_modified:
            return None

        if_modified_since = request.META.get("HTTP_IF_MODIFIED_SINCE", "")

        if if_modified_since:
            try:
                since = datetime.strptime(
                    if_modified_since,
                    "%a, %d %b %Y %H:%M:%S GMT",
                )
                modified = datetime.strptime(
                    last_modified,
                    "%a, %d %b %Y %H:%M:%S GMT",
                )

                if modified <= since:
                    response = JsonResponse({}, status=304)
                    response["Last-Modified"] = last_modified
                    return response
            except ValueError:
                pass

        return None
