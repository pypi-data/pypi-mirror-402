"""
SwiftAPI API Versioning.

Support for URL, header, and query parameter versioning.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from django.urls import re_path

from swiftapi.exceptions import APIException

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest

    from swiftapi.viewsets import ViewSet


class VersioningError(APIException):
    """Exception for versioning errors."""

    status_code = 400
    default_code = "invalid_version"
    default_detail = "Invalid or unsupported API version."


class BaseVersioning:
    """
    Base class for API versioning.
    """

    default_version: str | None = None
    allowed_versions: list[str] | None = None

    def determine_version(
        self,
        request: HttpRequest,
        **kwargs: Any,
    ) -> str | None:
        """
        Determine the API version from the request.

        Args:
            request: HTTP request
            **kwargs: URL kwargs

        Returns:
            Version string or None
        """
        raise NotImplementedError

    def is_allowed_version(self, version: str) -> bool:
        """Check if version is allowed."""
        if self.allowed_versions is None:
            return True
        return version in self.allowed_versions

    def get_version(
        self,
        request: HttpRequest,
        **kwargs: Any,
    ) -> str | None:
        """
        Get and validate the API version.

        Raises VersioningError if version is not allowed.
        """
        version = self.determine_version(request, **kwargs)

        if version is None:
            version = self.default_version

        if version and not self.is_allowed_version(version):
            raise VersioningError(
                f"Version '{version}' is not supported. "
                f"Allowed versions: {', '.join(self.allowed_versions or [])}"
            )

        return version


class URLPathVersioning(BaseVersioning):
    """
    URL path versioning.

    Version extracted from URL path:
    - /api/v1/users/
    - /api/v2/users/

    Configuration:
        SWIFTAPI = {
            "DEFAULT_VERSION": "v1",
            "ALLOWED_VERSIONS": ["v1", "v2"],
        }
    """

    version_param = "version"

    def __init__(
        self,
        default_version: str | None = None,
        allowed_versions: list[str] | None = None,
    ) -> None:
        from swiftapi.conf import settings

        self.default_version = default_version or settings.DEFAULT_VERSION
        self.allowed_versions = allowed_versions or settings.ALLOWED_VERSIONS or None

    def determine_version(
        self,
        request: HttpRequest,
        **kwargs: Any,
    ) -> str | None:
        """Get version from URL path parameter."""
        return kwargs.get(self.version_param)


class HeaderVersioning(BaseVersioning):
    """
    Header-based versioning.

    Version from Accept header:
    - Accept: application/json; version=1
    - Accept: application/vnd.api+json; version=2

    Or custom header:
    - X-API-Version: 1
    """

    header_name = "HTTP_X_API_VERSION"
    accept_header_pattern = r"version=(\d+)"

    def __init__(
        self,
        header_name: str | None = None,
        default_version: str | None = None,
        allowed_versions: list[str] | None = None,
    ) -> None:
        from swiftapi.conf import settings

        if header_name:
            self.header_name = f"HTTP_{header_name.upper().replace('-', '_')}"

        self.default_version = default_version or settings.DEFAULT_VERSION
        self.allowed_versions = allowed_versions or settings.ALLOWED_VERSIONS or None

    def determine_version(
        self,
        request: HttpRequest,
        **kwargs: Any,
    ) -> str | None:
        """Get version from header."""
        # Try custom header first
        version = request.META.get(self.header_name)
        if version:
            return version

        # Try Accept header
        accept = request.META.get("HTTP_ACCEPT", "")
        match = re.search(self.accept_header_pattern, accept)
        if match:
            return match.group(1)

        return None


class QueryParameterVersioning(BaseVersioning):
    """
    Query parameter versioning.

    Version from query string:
    - /api/users/?version=1
    """

    version_param = "version"

    def __init__(
        self,
        version_param: str | None = None,
        default_version: str | None = None,
        allowed_versions: list[str] | None = None,
    ) -> None:
        from swiftapi.conf import settings

        if version_param:
            self.version_param = version_param
        else:
            self.version_param = settings.VERSION_PARAM

        self.default_version = default_version or settings.DEFAULT_VERSION
        self.allowed_versions = allowed_versions or settings.ALLOWED_VERSIONS or None

    def determine_version(
        self,
        request: HttpRequest,
        **kwargs: Any,
    ) -> str | None:
        """Get version from query parameter."""
        return request.GET.get(self.version_param)


class NamespaceVersioning(BaseVersioning):
    """
    Namespace-based versioning.

    Uses Django URL namespaces:
    - namespace='v1'
    - namespace='v2'
    """

    def determine_version(
        self,
        request: HttpRequest,
        **kwargs: Any,
    ) -> str | None:
        """Get version from URL namespace."""
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match:
            namespace = resolver_match.namespace
            if namespace:
                # Extract version from namespace (e.g., "api-v1" -> "v1")
                parts = namespace.split("-")
                for part in parts:
                    if part.startswith("v") and part[1:].isdigit():
                        return part
        return None


class VersionedRouter:
    """
    Router that supports multiple API versions.

    Usage:
        from swiftapi.versioning import VersionedRouter

        router = VersionedRouter()

        # Register v1 viewsets
        router.register("users", UserViewSetV1, version="v1")

        # Register v2 viewsets
        router.register("users", UserViewSetV2, version="v2")

        # URLs: /api/v1/users/, /api/v2/users/
    """

    def __init__(
        self,
        allowed_versions: list[str] | None = None,
        default_version: str | None = None,
    ) -> None:
        """
        Initialize versioned router.

        Args:
            allowed_versions: List of valid versions
            default_version: Default version if not specified
        """
        self._registry: dict[str, list[tuple[str, type, str]]] = {}
        self.allowed_versions = allowed_versions or ["v1"]
        self.default_version = default_version or self.allowed_versions[0]

    def register(
        self,
        prefix: str,
        viewset: type[ViewSet],
        version: str | None = None,
        basename: str | None = None,
    ) -> None:
        """
        Register a ViewSet for a specific version.

        Args:
            prefix: URL prefix
            viewset: ViewSet class
            version: API version (default: default_version)
            basename: Base name for URL names
        """
        version = version or self.default_version

        if version not in self._registry:
            self._registry[version] = []

        if basename is None:
            basename = prefix.replace("/", "-")

        self._registry[version].append((prefix, viewset, basename))

    @property
    def urls(self):
        """Generate versioned URL patterns."""
        return self.get_urls()

    def get_urls(self):
        """Generate versioned URL patterns."""
        from swiftapi.routing import Router

        patterns = []

        for version, registrations in self._registry.items():
            # Create a router for this version
            version_router = Router()

            for prefix, viewset, basename in registrations:
                version_router.register(prefix, viewset, basename=basename)

            # Add version prefix to all URLs
            for pattern in version_router.urls:
                versioned_pattern = re_path(
                    rf"^{version}/{pattern.pattern.regex.pattern.lstrip('^')}",
                    pattern.callback,
                    name=f"{version}-{pattern.name}" if pattern.name else None,
                )
                patterns.append(versioned_pattern)

        return patterns


class VersionTransform:
    """
    Transform data between API versions.

    Usage:
        class UserTransform(VersionTransform):
            @staticmethod
            def v1_to_v2(data):
                data['full_name'] = f"{data.pop('first_name')} {data.pop('last_name')}"
                return data
    """

    @classmethod
    def transform(
        cls,
        data: Any,
        from_version: str,
        to_version: str,
    ) -> Any:
        """
        Transform data between versions.

        Args:
            data: Data to transform
            from_version: Source version
            to_version: Target version

        Returns:
            Transformed data
        """
        method_name = f"{from_version}_to_{to_version}"
        method = getattr(cls, method_name, None)

        if method:
            return method(data)

        return data


def version_view(versions: dict[str, Callable]) -> Callable:
    """
    Decorator to select handler based on API version.

    Usage:
        class UserViewSet(ViewSet):
            @version_view({
                "v1": "list_v1",
                "v2": "list_v2",
            })
            async def list(self, request):
                # Default implementation
                ...

            async def list_v1(self, request):
                # V1 implementation
                ...

            async def list_v2(self, request):
                # V2 implementation
                ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            version = getattr(request, "version", None)

            if version and version in versions:
                method_name = versions[version]
                method = getattr(self, method_name, None)
                if method:
                    return await method(request, *args, **kwargs)

            return await func(self, request, *args, **kwargs)

        return wrapper
    return decorator


import functools
