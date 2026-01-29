"""
SwiftAPI Domain Events and Signals.

Event system for reacting to CRUD operations with async support.
"""

from __future__ import annotations

import asyncio
import functools
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest



@dataclass
class Event:
    """
    Domain event carrying context information.
    """

    name: str
    data: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = None
    user_id: int | str | None = None
    tenant_id: int | str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Unique event identifier."""
        return f"{self.name}:{self.timestamp.isoformat()}:{uuid4().hex[:8]}"


class EventBus:
    """
    Central event bus for publishing and subscribing to events.

    Usage:
        from swiftapi.events import event_bus

        # Subscribe to events
        @event_bus.on("user.created")
        async def on_user_created(event):
            print(f"User created: {event.data}")

        # Publish events
        await event_bus.emit("user.created", user_data)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = {}
        self._wildcard_handlers: list[Callable] = []

    def on(
        self,
        event_name: str,
        handler: Callable | None = None,
    ) -> Callable:
        """
        Subscribe to an event.

        Can be used as a decorator or called directly.

        Args:
            event_name: Event name to subscribe to (supports wildcards: "user.*")
            handler: Handler function (optional if used as decorator)
        """
        def decorator(func: Callable) -> Callable:
            if "*" in event_name:
                self._wildcard_handlers.append((event_name, func))
            else:
                if event_name not in self._handlers:
                    self._handlers[event_name] = []
                self._handlers[event_name].append(func)
            return func

        if handler:
            return decorator(handler)
        return decorator

    def off(self, event_name: str, handler: Callable) -> None:
        """
        Unsubscribe from an event.

        Args:
            event_name: Event name
            handler: Handler to remove
        """
        if event_name in self._handlers:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name]
                if h != handler
            ]

    async def emit(
        self,
        event_name: str,
        data: Any = None,
        request: HttpRequest | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Emit an event to all subscribers.

        Events are processed asynchronously and don't block.

        Args:
            event_name: Event name
            data: Event payload
            request: HTTP request (for context)
            **kwargs: Additional event metadata
        """
        event = self._create_event(event_name, data, request, **kwargs)

        # Get all matching handlers
        handlers = list(self._handlers.get(event_name, []))

        # Add wildcard matches
        for pattern, handler in self._wildcard_handlers:
            if self._matches_pattern(event_name, pattern):
                handlers.append(handler)

        # Execute handlers asynchronously
        tasks = []
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(event))
            else:
                # Run sync handler in executor
                loop = asyncio.get_event_loop()
                tasks.append(
                    loop.run_in_executor(None, handler, event)
                )

        # Fire and forget - don't wait for handlers
        if tasks:
            asyncio.gather(*tasks, return_exceptions=True)

    def emit_sync(
        self,
        event_name: str,
        data: Any = None,
        request: HttpRequest | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Emit an event synchronously (for use outside async context).
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule for later execution
                asyncio.create_task(
                    self.emit(event_name, data, request, **kwargs)
                )
            else:
                loop.run_until_complete(
                    self.emit(event_name, data, request, **kwargs)
                )
        except RuntimeError:
            # No event loop, create one
            asyncio.run(self.emit(event_name, data, request, **kwargs))

    def _create_event(
        self,
        event_name: str,
        data: Any,
        request: HttpRequest | None,
        **kwargs: Any,
    ) -> Event:
        """Create an Event object with context."""
        user_id = None
        tenant_id = None
        request_id = None

        if request:
            if hasattr(request, "user") and request.user.is_authenticated:
                user_id = request.user.pk
            if hasattr(request, "tenant"):
                tenant_id = getattr(request.tenant, "pk", request.tenant)
            request_id = getattr(request, "request_id", None)

        return Event(
            name=event_name,
            data=data,
            user_id=user_id,
            tenant_id=tenant_id,
            request_id=request_id,
            metadata=kwargs,
        )

    def _matches_pattern(self, event_name: str, pattern: str) -> bool:
        """Check if event name matches wildcard pattern."""
        import fnmatch
        return fnmatch.fnmatch(event_name, pattern)


# Global event bus instance
event_bus = EventBus()


# Pre-defined CRUD event names
class CRUDEvents:
    """Standard CRUD event names."""

    PRE_CREATE = "pre_create"
    POST_CREATE = "post_create"
    PRE_UPDATE = "pre_update"
    POST_UPDATE = "post_update"
    PRE_DELETE = "pre_delete"
    POST_DELETE = "post_delete"
    PRE_LIST = "pre_list"
    POST_LIST = "post_list"
    PRE_RETRIEVE = "pre_retrieve"
    POST_RETRIEVE = "post_retrieve"

    @classmethod
    def for_model(cls, model_name: str, action: str) -> str:
        """Get event name for a model and action."""
        return f"{model_name.lower()}.{action}"


class EventEmitterMixin:
    """
    Mixin for ViewSets to automatically emit CRUD events.

    Usage:
        class UserViewSet(EventEmitterMixin, ViewSet):
            model = User
            ...

        # Events emitted:
        # - user.pre_create, user.post_create
        # - user.pre_update, user.post_update
        # - user.pre_delete, user.post_delete
    """

    emit_events: bool = True

    def _get_model_name(self) -> str:
        """Get model name for event naming."""
        if hasattr(self, "model") and self.model:
            return self.model.__name__
        return self.__class__.__name__.replace("ViewSet", "")

    async def _emit_event(
        self,
        action: str,
        data: Any = None,
        request: HttpRequest | None = None,
    ) -> None:
        """Emit a CRUD event."""
        if not self.emit_events:
            return

        event_name = CRUDEvents.for_model(self._get_model_name(), action)
        await event_bus.emit(event_name, data, request)

    async def create(self, request):
        """Create with events."""
        await self._emit_event(CRUDEvents.PRE_CREATE, None, request)
        result = await super().create(request)  # type: ignore
        await self._emit_event(CRUDEvents.POST_CREATE, result, request)
        return result

    async def update(self, request, pk):
        """Update with events."""
        await self._emit_event(CRUDEvents.PRE_UPDATE, {"pk": pk}, request)
        result = await super().update(request, pk)  # type: ignore
        await self._emit_event(CRUDEvents.POST_UPDATE, result, request)
        return result

    async def partial_update(self, request, pk):
        """Partial update with events."""
        await self._emit_event(CRUDEvents.PRE_UPDATE, {"pk": pk}, request)
        result = await super().partial_update(request, pk)  # type: ignore
        await self._emit_event(CRUDEvents.POST_UPDATE, result, request)
        return result

    async def destroy(self, request, pk):
        """Delete with events."""
        await self._emit_event(CRUDEvents.PRE_DELETE, {"pk": pk}, request)
        result = await super().destroy(request, pk)  # type: ignore
        await self._emit_event(CRUDEvents.POST_DELETE, {"pk": pk}, request)
        return result


# Convenience decorators

def on_event(event_name: str) -> Callable:
    """
    Decorator to subscribe a function to an event.

    Usage:
        @on_event("user.post_create")
        async def send_welcome_email(event):
            user = event.data
            await send_email(user.email, "Welcome!")
    """
    return event_bus.on(event_name)


def emit(event_name: str, data: Any = None, **kwargs: Any) -> Callable:
    """
    Decorator to emit an event after a function executes.

    Usage:
        @emit("order.completed")
        async def complete_order(order):
            order.status = "completed"
            await order.asave()
            return order
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kw: Any) -> Any:
            result = await func(*args, **kw)
            await event_bus.emit(event_name, data or result, **kwargs)
            return result
        return wrapper
    return decorator
