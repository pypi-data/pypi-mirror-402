"""
SwiftAPI Request Handler.

Async request processing pipeline with authentication, permissions,
and response serialization.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from django.http import HttpRequest, JsonResponse

from swiftapi.conf import settings
from swiftapi.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    PermissionDenied,
    default_exception_handler,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from swiftapi.viewsets import ViewSet


logger = logging.getLogger("swiftapi")


class RequestContext:
    """
    Context object carrying request metadata through the pipeline.
    """

    def __init__(self, request: HttpRequest) -> None:
        self.request = request
        self.request_id = self._get_or_create_request_id(request)
        self.start_time = time.perf_counter()
        self.user = getattr(request, "user", None)
        self.tenant = getattr(request, "tenant", None)
        self.action = ""
        self.viewset: ViewSet | None = None

    def _get_or_create_request_id(self, request: HttpRequest) -> str:
        """Get request ID from header or generate one."""
        header_name = "HTTP_" + settings.REQUEST_ID_HEADER.upper().replace("-", "_")
        request_id = request.META.get(header_name)

        if not request_id and settings.GENERATE_REQUEST_ID:
            request_id = str(uuid.uuid4())[:8]

        return request_id or ""

    @property
    def duration_ms(self) -> float:
        """Get request duration in milliseconds."""
        return (time.perf_counter() - self.start_time) * 1000


def create_handler(
    viewset_class: type[ViewSet],
    actions: dict[str, str],
    initkwargs: dict[str, Any],
) -> Callable:
    """
    Create an async view handler for a ViewSet.

    This is the main entry point that bridges Django's URL routing
    to SwiftAPI's async ViewSet handling.

    Args:
        viewset_class: The ViewSet class
        actions: Mapping of HTTP methods to action names
        initkwargs: Additional kwargs for ViewSet initialization

    Returns:
        Async view function compatible with Django
    """

    async def view(request: HttpRequest, **kwargs: Any) -> JsonResponse:
        """Async view handler."""
        context = RequestContext(request)

        try:
            # Log request start
            if settings.ENABLE_REQUEST_LOGGING:
                logger.info(
                    f"[{context.request_id}] {request.method} {request.path}",
                    extra={
                        "request_id": context.request_id,
                        "method": request.method,
                        "path": request.path,
                    },
                )

            # Get action for this HTTP method
            method = request.method.lower()
            action_name = actions.get(method)

            if action_name is None:
                raise MethodNotAllowed(request.method)

            context.action = action_name

            # Initialize ViewSet
            viewset = viewset_class(request=request, **kwargs)
            viewset.action = action_name
            context.viewset = viewset

            # Run authentication
            await run_authentication(request, viewset)

            # Run permission checks
            await check_permissions(request, viewset)

            # Get the action handler
            handler = getattr(viewset, action_name, None)
            if handler is None:
                raise MethodNotAllowed(request.method)

            # Execute the handler
            if asyncio.iscoroutinefunction(handler):
                if "pk" in kwargs:
                    result = await handler(request, kwargs["pk"])
                else:
                    result = await handler(request)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                if "pk" in kwargs:
                    result = await loop.run_in_executor(
                        None,
                        functools.partial(handler, request, kwargs["pk"]),
                    )
                else:
                    result = await loop.run_in_executor(
                        None,
                        functools.partial(handler, request),
                    )

            # Serialize response
            response = create_response(result, viewset, action_name)

            # Log success
            if settings.ENABLE_REQUEST_LOGGING:
                logger.info(
                    f"[{context.request_id}] {response.status_code} "
                    f"({context.duration_ms:.1f}ms)",
                    extra={
                        "request_id": context.request_id,
                        "status_code": response.status_code,
                        "duration_ms": context.duration_ms,
                    },
                )

            # Add request ID header
            response[settings.REQUEST_ID_HEADER] = context.request_id

            return response

        except Exception as exc:
            # Log error
            if settings.ENABLE_REQUEST_LOGGING:
                logger.error(
                    f"[{context.request_id}] Error: {exc}",
                    extra={
                        "request_id": context.request_id,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    exc_info=True,
                )

            # Handle exception
            response = default_exception_handler(exc, request)
            response[settings.REQUEST_ID_HEADER] = context.request_id
            return response

    # Make it work with Django's URL resolver
    view.viewset_class = viewset_class  # type: ignore
    view.actions = actions  # type: ignore
    view.initkwargs = initkwargs  # type: ignore

    # Add ASGI/WSGI compatibility
    return async_to_sync_view(view)


def async_to_sync_view(async_view: Callable) -> Callable:
    """
    Wrap an async view for compatibility with sync Django.

    In ASGI, the view runs natively async.
    In WSGI, it runs via asyncio.run() or an existing loop.
    """
    @functools.wraps(async_view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in async context, but this is a sync call
            # This shouldn't happen in properly configured async Django
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(async_view(request, *args, **kwargs))
        except RuntimeError:
            # No running loop - we're in sync context
            return asyncio.run(async_view(request, *args, **kwargs))

    # Preserve async view for ASGI
    wrapper._async_view = async_view  # type: ignore

    # Make it async-native for ASGI
    async def async_wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        return await async_view(request, *args, **kwargs)

    wrapper._is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore

    return wrapper


async def run_authentication(request: HttpRequest, viewset: ViewSet) -> None:
    """
    Run authentication backends.

    Sets request.user and request.auth.
    """
    from swiftapi.conf import import_from_string

    # Get authentication classes
    auth_classes = getattr(viewset, "authentication_classes", None)
    if auth_classes is None:
        auth_classes = settings.DEFAULT_AUTHENTICATION_CLASSES

    user = None
    auth = None

    for auth_class_path in auth_classes:
        try:
            auth_class = import_from_string(auth_class_path, "authentication_classes")
            authenticator = auth_class()

            if asyncio.iscoroutinefunction(authenticator.authenticate):
                result = await authenticator.authenticate(request)
            else:
                result = authenticator.authenticate(request)

            if result is not None:
                user, auth = result
                break
        except AuthenticationFailed:
            raise
        except Exception:
            continue

    # Set user on request if authenticated
    if user is not None:
        request.user = user
        request.auth = auth  # type: ignore


async def check_permissions(request: HttpRequest, viewset: ViewSet) -> None:
    """
    Check all permissions for the ViewSet.

    Raises PermissionDenied if any permission fails.
    """
    from swiftapi.conf import import_from_string

    # Get permission classes
    permission_classes = getattr(viewset, "permission_classes", None)
    if permission_classes is None:
        permission_classes = []
        for path in settings.DEFAULT_PERMISSION_CLASSES:
            permission_classes.append(import_from_string(path, "permission_classes"))

    for permission_class in permission_classes:
        if isinstance(permission_class, str):
            permission_class = import_from_string(permission_class, "permission_classes")

        permission = permission_class() if isinstance(permission_class, type) else permission_class

        # Check permission
        if asyncio.iscoroutinefunction(permission.has_permission):
            has_perm = await permission.has_permission(request, viewset)
        else:
            has_perm = permission.has_permission(request, viewset)

        if not has_perm:
            message = getattr(permission, "message", "Permission denied.")
            raise PermissionDenied(message)


def create_response(
    data: Any,
    viewset: ViewSet,
    action: str,
) -> JsonResponse:
    """
    Create a JSON response from handler result.

    Args:
        data: Handler return value
        viewset: ViewSet instance
        action: Action name

    Returns:
        JsonResponse
    """
    # Handle None response (e.g., delete)
    if data is None:
        return JsonResponse({}, status=204)

    # Serialize with schema if available
    if viewset.read_schema:
        many = action == "list"
        serialized = viewset.read_schema.serialize(data, many=many)
    else:
        serialized = viewset.serialize(data, many=(action == "list"))

    # Determine status code
    status = 200
    if action == "create":
        status = 201

    # Wrap in data key for consistency
    response_data = {"data": serialized}

    return JsonResponse(response_data, status=status)


class LifecycleHooks:
    """
    Mixin for ViewSets providing lifecycle hooks.
    """

    async def before_request(self, request: HttpRequest, action: str) -> None:
        """Hook called before action execution."""
        pass

    async def after_request(
        self,
        request: HttpRequest,
        action: str,
        response: Any,
    ) -> Any:
        """Hook called after action execution. Can modify response."""
        return response

    async def on_error(
        self,
        request: HttpRequest,
        action: str,
        error: Exception,
    ) -> Exception | None:
        """Hook called when an error occurs. Can suppress or modify error."""
        return error
