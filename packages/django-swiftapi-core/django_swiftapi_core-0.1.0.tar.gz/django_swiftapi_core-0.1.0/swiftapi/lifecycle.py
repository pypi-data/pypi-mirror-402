"""
SwiftAPI Request Lifecycle Hooks.

Hooks for processing requests at various stages.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest

    from swiftapi.viewsets import ViewSet


class LifecycleHook:
    """
    Represents a lifecycle hook.
    """

    def __init__(
        self,
        stage: str,
        func: Callable,
        priority: int = 0,
    ) -> None:
        self.stage = stage
        self.func = func
        self.priority = priority


class LifecycleManager:
    """
    Manages request lifecycle hooks.

    Stages:
    - before_request: Before handler execution
    - after_request: After handler execution (can modify response)
    - on_error: When an exception occurs
    - on_success: When handler completes successfully
    """

    def __init__(self) -> None:
        self._hooks: dict[str, list[LifecycleHook]] = {
            "before_request": [],
            "after_request": [],
            "on_error": [],
            "on_success": [],
        }

    def register(
        self,
        stage: str,
        func: Callable,
        priority: int = 0,
    ) -> None:
        """
        Register a lifecycle hook.

        Args:
            stage: Lifecycle stage
            func: Hook function
            priority: Execution priority (lower runs first)
        """
        if stage not in self._hooks:
            raise ValueError(f"Invalid stage: {stage}")

        hook = LifecycleHook(stage, func, priority)
        self._hooks[stage].append(hook)
        self._hooks[stage].sort(key=lambda h: h.priority)

    async def run_before_request(
        self,
        request: HttpRequest,
        view: ViewSet,
        action: str,
    ) -> None:
        """Run before_request hooks."""
        for hook in self._hooks["before_request"]:
            await self._call_hook(hook.func, request, view, action)

    async def run_after_request(
        self,
        request: HttpRequest,
        view: ViewSet,
        action: str,
        response: Any,
    ) -> Any:
        """Run after_request hooks. Can modify response."""
        for hook in self._hooks["after_request"]:
            result = await self._call_hook(hook.func, request, view, action, response)
            if result is not None:
                response = result
        return response

    async def run_on_error(
        self,
        request: HttpRequest,
        view: ViewSet | None,
        action: str,
        error: Exception,
    ) -> Exception | None:
        """Run on_error hooks. Can suppress or modify error."""
        for hook in self._hooks["on_error"]:
            result = await self._call_hook(hook.func, request, view, action, error)
            if result is None:
                return None  # Error suppressed
            if isinstance(result, Exception):
                error = result
        return error

    async def run_on_success(
        self,
        request: HttpRequest,
        view: ViewSet,
        action: str,
        result: Any,
    ) -> None:
        """Run on_success hooks."""
        for hook in self._hooks["on_success"]:
            await self._call_hook(hook.func, request, view, action, result)

    async def _call_hook(self, func: Callable, *args: Any) -> Any:
        """Call a hook function."""
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return await func(*args)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, functools.partial(func, *args)
            )


# Global lifecycle manager
lifecycle_manager = LifecycleManager()


# Decorator shortcuts

def before_request(priority: int = 0) -> Callable:
    """
    Decorator to register a before_request hook.

    Usage:
        @before_request()
        async def log_request(request, view, action):
            logger.info(f"Request: {action}")
    """
    def decorator(func: Callable) -> Callable:
        lifecycle_manager.register("before_request", func, priority)
        return func
    return decorator


def after_request(priority: int = 0) -> Callable:
    """
    Decorator to register an after_request hook.

    Usage:
        @after_request()
        async def add_timing_header(request, view, action, response):
            response["X-Response-Time"] = "..."
            return response
    """
    def decorator(func: Callable) -> Callable:
        lifecycle_manager.register("after_request", func, priority)
        return func
    return decorator


def on_error(priority: int = 0) -> Callable:
    """
    Decorator to register an on_error hook.

    Usage:
        @on_error()
        async def handle_error(request, view, action, error):
            logger.error(f"Error in {action}: {error}")
            return error  # Or return None to suppress
    """
    def decorator(func: Callable) -> Callable:
        lifecycle_manager.register("on_error", func, priority)
        return func
    return decorator


def on_success(priority: int = 0) -> Callable:
    """
    Decorator to register an on_success hook.

    Usage:
        @on_success()
        async def log_success(request, view, action, result):
            logger.info(f"Success: {action}")
    """
    def decorator(func: Callable) -> Callable:
        lifecycle_manager.register("on_success", func, priority)
        return func
    return decorator


class LifecycleMixin:
    """
    Mixin for ViewSets to add lifecycle hook methods.

    Usage:
        class UserViewSet(LifecycleMixin, ViewSet):
            async def before_request(self, request, action):
                # Called before every action
                pass

            async def after_request(self, request, action, response):
                # Called after every action
                return response

            async def on_create(self, request, data):
                # Called before create action
                pass

            async def on_created(self, request, obj):
                # Called after create action
                pass
    """

    async def before_request(self, request: HttpRequest, action: str) -> None:
        """Hook called before any action."""
        pass

    async def after_request(
        self,
        request: HttpRequest,
        action: str,
        response: Any,
    ) -> Any:
        """Hook called after any action. Can modify response."""
        return response

    async def on_error(
        self,
        request: HttpRequest,
        action: str,
        error: Exception,
    ) -> Exception | None:
        """Hook called on error. Return None to suppress."""
        return error

    # Action-specific hooks

    async def on_list(self, request: HttpRequest, queryset: Any) -> Any:
        """Hook before list action. Can modify queryset."""
        return queryset

    async def on_retrieve(self, request: HttpRequest, obj: Any) -> Any:
        """Hook before returning object in retrieve."""
        return obj

    async def on_create(self, request: HttpRequest, data: dict) -> dict:
        """Hook before creating object. Can modify data."""
        return data

    async def on_created(self, request: HttpRequest, obj: Any) -> None:
        """Hook after object is created."""
        pass

    async def on_update(self, request: HttpRequest, obj: Any, data: dict) -> dict:
        """Hook before updating object. Can modify data."""
        return data

    async def on_updated(self, request: HttpRequest, obj: Any) -> None:
        """Hook after object is updated."""
        pass

    async def on_delete(self, request: HttpRequest, obj: Any) -> None:
        """Hook before deleting object."""
        pass

    async def on_deleted(self, request: HttpRequest, pk: Any) -> None:
        """Hook after object is deleted."""
        pass


class TransactionMixin:
    """
    Mixin for ViewSets to wrap actions in database transactions.

    Usage:
        class UserViewSet(TransactionMixin, ViewSet):
            atomic_actions = ["create", "update", "partial_update", "destroy"]
    """

    atomic_actions: list[str] = ["create", "update", "partial_update", "destroy"]

    async def dispatch(self, request: HttpRequest, action: str, *args: Any, **kwargs: Any) -> Any:
        """Wrap action in transaction if atomic."""
        from django.db import transaction

        handler = getattr(self, action, None)

        if action in self.atomic_actions and handler:
            async with transaction.atomic():
                return await handler(request, *args, **kwargs)
        elif handler:
            return await handler(request, *args, **kwargs)
        else:
            from swiftapi.exceptions import MethodNotAllowed
            raise MethodNotAllowed(request.method)
