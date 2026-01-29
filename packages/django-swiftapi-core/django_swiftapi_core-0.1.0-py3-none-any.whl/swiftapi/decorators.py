"""
SwiftAPI Decorators.

View function decorators - similar to DRF's decorators.py.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


def api_view(methods: list[str] | None = None) -> Callable:
    """
    Decorator for function-based API views.

    Example:
        @api_view(["GET", "POST"])
        async def user_list(request):
            if request.method == "GET":
                return JsonResponse({"users": []})
            ...
    """
    methods = methods or ["GET"]
    methods = [m.upper() for m in methods]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            from swiftapi.exceptions import MethodNotAllowed

            if request.method not in methods:
                raise MethodNotAllowed(method=request.method)

            # Parse JSON body
            if request.method in ("POST", "PUT", "PATCH"):
                import json
                try:
                    request.data = json.loads(request.body.decode("utf-8"))
                except (json.JSONDecodeError, ValueError):
                    request.data = {}

            return await func(request, *args, **kwargs)

        wrapper.methods = methods
        return wrapper

    return decorator


def permission_classes(classes: list[type]) -> Callable:
    """
    Decorator to set permission classes for a view.

    Example:
        @api_view(["GET"])
        @permission_classes([IsAuthenticated])
        async def protected_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func.permission_classes = classes
        return func
    return decorator


def authentication_classes(classes: list[type]) -> Callable:
    """
    Decorator to set authentication classes for a view.

    Example:
        @api_view(["GET"])
        @authentication_classes([TokenAuthentication])
        async def api_endpoint(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func.authentication_classes = classes
        return func
    return decorator


def throttle_classes(classes: list[type]) -> Callable:
    """
    Decorator to set throttle classes for a view.

    Example:
        @api_view(["GET"])
        @throttle_classes([AnonRateThrottle])
        async def rate_limited_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func.throttle_classes = classes
        return func
    return decorator


def renderer_classes(classes: list[type]) -> Callable:
    """
    Decorator to set renderer classes for a view.

    Example:
        @api_view(["GET"])
        @renderer_classes([JSONRenderer, CSVRenderer])
        async def download_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func.renderer_classes = classes
        return func
    return decorator


def parser_classes(classes: list[type]) -> Callable:
    """
    Decorator to set parser classes for a view.

    Example:
        @api_view(["POST"])
        @parser_classes([JSONParser, FormParser])
        async def upload_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func.parser_classes = classes
        return func
    return decorator


def schema(schema_class: type) -> Callable:
    """
    Decorator to set schema for a view (for OpenAPI generation).

    Example:
        @api_view(["POST"])
        @schema(UserCreateSchema)
        async def create_user(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func.schema = schema_class
        return func
    return decorator


class MethodMapper(dict):
    """
    Mapper for action decorator to track which HTTP methods map to which actions.

    Used internally by the @action decorator.
    """

    def __init__(self, action: Callable, methods: list[str]) -> None:
        super().__init__()
        self.action = action
        for method in methods:
            self[method.lower()] = action.__name__


def action(
    detail: bool = True,
    methods: list[str] | None = None,
    url_path: str | None = None,
    url_name: str | None = None,
    permission_classes: list[type] | None = None,
    authentication_classes: list[type] | None = None,
    throttle_classes: list[type] | None = None,
    **kwargs: Any,
) -> Callable:
    """
    Decorator for custom ViewSet actions.

    Example:
        class UserViewSet(ViewSet):
            @action(detail=True, methods=["POST"])
            async def reset_password(self, request, pk):
                ...

            @action(detail=False, methods=["GET"])
            async def me(self, request):
                ...
    """
    methods = methods or ["GET"]
    methods = [m.upper() for m in methods]

    def decorator(func: Callable) -> Callable:
        func._is_action = True
        func.detail = detail
        func.methods = methods
        func.url_path = url_path or func.__name__
        func.url_name = url_name or func.__name__.replace("_", "-")
        func.kwargs = kwargs
        func.mapping = MethodMapper(func, methods)

        if permission_classes is not None:
            func.permission_classes = permission_classes
        if authentication_classes is not None:
            func.authentication_classes = authentication_classes
        if throttle_classes is not None:
            func.throttle_classes = throttle_classes

        return func

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "MethodMapper",
    "action",
    "api_view",
    "authentication_classes",
    "parser_classes",
    "permission_classes",
    "renderer_classes",
    "schema",
    "throttle_classes",
]
