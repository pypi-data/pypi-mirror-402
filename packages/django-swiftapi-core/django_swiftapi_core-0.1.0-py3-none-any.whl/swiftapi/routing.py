"""
SwiftAPI Router System.

DRF-like router for automatic URL generation from ViewSets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.urls import re_path

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.urls.resolvers import URLPattern

    from swiftapi.viewsets import ViewSet


class Route:
    """
    Represents a single URL route configuration.
    """

    def __init__(
        self,
        url: str,
        mapping: dict[str, str],
        name: str,
        detail: bool,
        initkwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize a route.

        Args:
            url: URL pattern string
            mapping: HTTP method to ViewSet action mapping
            name: URL name suffix
            detail: If True, this is a detail route (requires pk)
            initkwargs: Additional kwargs for view initialization
        """
        self.url = url
        self.mapping = mapping
        self.name = name
        self.detail = detail
        self.initkwargs = initkwargs or {}


class Router:
    """
    Router for generating URL patterns from ViewSets.

    Similar to DRF's DefaultRouter, provides automatic URL generation
    for RESTful endpoints.

    Example:
        from swiftapi import Router
        from myapp.views import UserViewSet, PostViewSet

        router = Router()
        router.register("users", UserViewSet)
        router.register("posts", PostViewSet, basename="blog-posts")

        # In urls.py
        urlpatterns = [
            path("api/v1/", include(router.urls)),
        ]

    Generated URLs:
        GET    /api/v1/users/          -> UserViewSet.list
        POST   /api/v1/users/          -> UserViewSet.create
        GET    /api/v1/users/{pk}/     -> UserViewSet.retrieve
        PUT    /api/v1/users/{pk}/     -> UserViewSet.update
        PATCH  /api/v1/users/{pk}/     -> UserViewSet.partial_update
        DELETE /api/v1/users/{pk}/     -> UserViewSet.destroy
    """

    # Standard routes for CRUD operations
    routes: list[Route] = [
        # List route
        Route(
            url=r"^{prefix}/$",
            mapping={
                "get": "list",
                "post": "create",
            },
            name="{basename}-list",
            detail=False,
        ),
        # Detail route
        Route(
            url=r"^{prefix}/(?P<pk>[^/.]+)/$",
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            name="{basename}-detail",
            detail=True,
        ),
    ]

    def __init__(self) -> None:
        """Initialize the router."""
        self._registry: list[tuple[str, type[ViewSet], str]] = []

    def register(
        self,
        prefix: str,
        viewset: type[ViewSet],
        basename: str | None = None,
    ) -> None:
        """
        Register a ViewSet with the router.

        Args:
            prefix: URL prefix (e.g., "users")
            viewset: ViewSet class
            basename: Base name for URL names (defaults to prefix)
        """
        if basename is None:
            basename = prefix.replace("/", "-")

        self._registry.append((prefix, viewset, basename))

    def crud(
        self,
        prefix: str,
        model: type,
        *,
        basename: str | None = None,
        exclude: list[str] | None = None,
        read_only_fields: list[str] | None = None,
        permission_classes: list | None = None,
    ) -> None:
        """
        Register a model with auto-generated CRUD ViewSet.

        This is a convenience method for quickly creating CRUD APIs.

        Args:
            prefix: URL prefix
            model: Django model class
            basename: Base name for URLs
            exclude: Fields to exclude from schema
            read_only_fields: Fields that are read-only
            permission_classes: Permissions for the ViewSet

        Example:
            router.crud("users", User, exclude=["password"])
        """
        from swiftapi.crud import create_crud_viewset

        viewset = create_crud_viewset(
            model,
            exclude=exclude,
            read_only_fields=read_only_fields,
            permission_classes=permission_classes,
        )

        self.register(prefix, viewset, basename=basename)

    @property
    def urls(self) -> list[URLPattern]:
        """
        Generate URL patterns for all registered ViewSets.

        Returns:
            List of Django URL patterns
        """
        return self.get_urls()

    def get_urls(self) -> list[URLPattern]:
        """
        Generate URL patterns for all registered ViewSets.

        Returns:
            List of Django URL patterns
        """
        urls: list[URLPattern] = []

        for prefix, viewset, basename in self._registry:
            # Add standard routes
            urls.extend(self._get_routes_for_viewset(prefix, viewset, basename))

            # Add custom action routes
            urls.extend(self._get_custom_action_routes(prefix, viewset, basename))

        return urls

    def _get_routes_for_viewset(
        self,
        prefix: str,
        viewset: type[ViewSet],
        basename: str,
    ) -> list[URLPattern]:
        """Generate standard routes for a ViewSet."""
        urls: list[URLPattern] = []

        for route in self.routes:
            # Check which actions are available on this ViewSet
            mapping = self._get_available_actions(viewset, route.mapping)

            if not mapping:
                continue

            # Build URL pattern
            url_pattern = route.url.format(prefix=prefix)
            name = route.name.format(basename=basename)

            # Create view function
            view = self._create_view(viewset, mapping, route.initkwargs)

            urls.append(
                re_path(url_pattern, view, name=name)
            )

        return urls

    def _get_custom_action_routes(
        self,
        prefix: str,
        viewset: type[ViewSet],
        basename: str,
    ) -> list[URLPattern]:
        """Generate routes for custom actions."""
        urls: list[URLPattern] = []

        custom_actions = getattr(viewset, "_custom_actions", {})

        for action_name, config in custom_actions.items():
            detail = config.get("detail", True)
            url_path = config.get("url_path", action_name)
            url_name = config.get("url_name") or f"{basename}-{action_name}"
            methods = config.get("methods", ["GET"])

            # Build mapping
            mapping = {m.lower(): action_name for m in methods}

            # Build URL pattern
            if detail:
                pattern = rf"^{prefix}/(?P<pk>[^/.]+)/{url_path}/$"
            else:
                pattern = rf"^{prefix}/{url_path}/$"

            # Create view
            view = self._create_view(viewset, mapping, {})

            urls.append(
                re_path(pattern, view, name=url_name)
            )

        return urls

    def _get_available_actions(
        self,
        viewset: type[ViewSet],
        mapping: dict[str, str],
    ) -> dict[str, str]:
        """Filter mapping to only include actions available on the ViewSet."""
        available = {}

        for method, action_name in mapping.items():
            if hasattr(viewset, action_name):
                available[method] = action_name

        return available

    def _create_view(
        self,
        viewset: type[ViewSet],
        actions: dict[str, str],
        initkwargs: dict[str, Any],
    ) -> Callable:
        """
        Create a view function for the given ViewSet and actions.

        Args:
            viewset: ViewSet class
            actions: HTTP method to action mapping
            initkwargs: Additional initialization kwargs

        Returns:
            Async view function
        """
        from swiftapi.handlers import create_handler

        return create_handler(viewset, actions, initkwargs)


class SimpleRouter(Router):
    """
    Simple router without trailing slashes.

    URLs don't have trailing slashes.
    """

    routes = [
        Route(
            url=r"^{prefix}$",
            mapping={
                "get": "list",
                "post": "create",
            },
            name="{basename}-list",
            detail=False,
        ),
        Route(
            url=r"^{prefix}/(?P<pk>[^/.]+)$",
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            name="{basename}-detail",
            detail=True,
        ),
    ]


class NestedRouter(Router):
    """
    Router for nested resources.

    Example:
        parent_router = Router()
        parent_router.register("users", UserViewSet)

        nested_router = NestedRouter(parent_router, "users", lookup="user")
        nested_router.register("posts", PostViewSet)

        # Generated URLs:
        # /users/{user_pk}/posts/
        # /users/{user_pk}/posts/{pk}/
    """

    def __init__(
        self,
        parent_router: Router,
        parent_prefix: str,
        lookup: str = "parent",
    ) -> None:
        """
        Initialize nested router.

        Args:
            parent_router: Parent router instance
            parent_prefix: Prefix of parent resource
            lookup: Lookup field name for parent
        """
        super().__init__()
        self.parent_router = parent_router
        self.parent_prefix = parent_prefix
        self.lookup = lookup
        self.lookup_regex = r"(?P<{lookup}_pk>[^/.]+)"

    @property
    def routes(self) -> list[Route]:
        """Generate routes with parent prefix."""
        parent_pattern = f"^{self.parent_prefix}/{self.lookup_regex.format(lookup=self.lookup)}"

        return [
            Route(
                url=parent_pattern + r"/{prefix}/$",
                mapping={
                    "get": "list",
                    "post": "create",
                },
                name="{basename}-list",
                detail=False,
            ),
            Route(
                url=parent_pattern + r"/{prefix}/(?P<pk>[^/.]+)/$",
                mapping={
                    "get": "retrieve",
                    "put": "update",
                    "patch": "partial_update",
                    "delete": "destroy",
                },
                name="{basename}-detail",
                detail=True,
            ),
        ]
