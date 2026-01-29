"""
SwiftAPI Background Tasks.

Support for offloading work to background workers.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    pass


logger = logging.getLogger("swiftapi.tasks")


class TaskResult:
    """
    Result of a background task.
    """

    def __init__(
        self,
        task_id: str,
        status: str = "pending",
        result: Any = None,
        error: str | None = None,
    ) -> None:
        self.task_id = task_id
        self.status = status  # pending, running, completed, failed
        self.result = result
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class BaseTaskBackend:
    """
    Base class for task backends.
    """

    def delay(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> TaskResult:
        """
        Queue a task for background execution.

        Returns immediately with a TaskResult containing task_id.
        """
        raise NotImplementedError

    def get_result(self, task_id: str) -> TaskResult | None:
        """Get the result of a task by ID."""
        raise NotImplementedError


class AsyncTaskBackend(BaseTaskBackend):
    """
    Simple async task backend using asyncio.

    Tasks run in the background but within the same process.
    Good for development and light workloads.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskResult] = {}

    def delay(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> TaskResult:
        """Queue task using asyncio.create_task."""
        import uuid

        task_id = str(uuid.uuid4())
        result = TaskResult(task_id=task_id, status="pending")
        self._tasks[task_id] = result

        async def run_task():
            try:
                result.status = "running"
                if asyncio.iscoroutinefunction(func):
                    output = await func(*args, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    output = await loop.run_in_executor(
                        None, functools.partial(func, *args, **kwargs)
                    )
                result.result = output
                result.status = "completed"
            except Exception as e:
                result.error = str(e)
                result.status = "failed"
                logger.error(f"Task {task_id} failed: {e}", exc_info=True)

        try:
            asyncio.create_task(run_task())
        except RuntimeError:
            # No running event loop, run synchronously
            asyncio.run(run_task())

        return result

    def get_result(self, task_id: str) -> TaskResult | None:
        return self._tasks.get(task_id)


class CeleryTaskBackend(BaseTaskBackend):
    """
    Celery-based task backend for distributed task processing.

    Requires Celery: pip install celery

    Usage:
        # celery_app.py
        from celery import Celery
        app = Celery('myapp')

        # settings.py
        SWIFTAPI = {
            "TASK_BACKEND": "swiftapi.tasks.CeleryTaskBackend",
            "CELERY_APP": "myapp.celery_app.app",
        }
    """

    def __init__(self, celery_app: Any = None) -> None:
        self.celery_app = celery_app
        self._ensure_celery()

    def _ensure_celery(self) -> None:
        """Load Celery app from settings if not provided."""
        if self.celery_app is not None:
            return

        from swiftapi.conf import import_string, settings

        celery_app_path = getattr(settings, "CELERY_APP", None)
        if celery_app_path:
            self.celery_app = import_string(celery_app_path)

    def delay(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> TaskResult:
        """Queue task using Celery."""
        if self.celery_app is None:
            raise ValueError(
                "Celery app not configured. Set SWIFTAPI['CELERY_APP'] in settings."
            )

        # Create Celery task if not already decorated
        if not hasattr(func, "delay"):
            func = self.celery_app.task(func)

        async_result = func.delay(*args, **kwargs)

        return TaskResult(
            task_id=async_result.id,
            status="pending",
        )

    def get_result(self, task_id: str) -> TaskResult | None:
        """Get result from Celery."""
        if self.celery_app is None:
            return None

        async_result = self.celery_app.AsyncResult(task_id)

        status_map = {
            "PENDING": "pending",
            "STARTED": "running",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "RETRY": "running",
        }

        return TaskResult(
            task_id=task_id,
            status=status_map.get(async_result.status, "unknown"),
            result=async_result.result if async_result.ready() else None,
            error=str(async_result.result) if async_result.failed() else None,
        )


class DjangoQTaskBackend(BaseTaskBackend):
    """
    Django-Q based task backend.

    Requires: pip install django-q2
    """

    def delay(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> TaskResult:
        """Queue task using Django-Q."""
        try:
            from django_q.tasks import async_task
        except ImportError:
            raise ValueError("django-q2 is required. Install with: pip install django-q2")

        task_id = async_task(func, *args, **kwargs)

        return TaskResult(task_id=task_id, status="pending")

    def get_result(self, task_id: str) -> TaskResult | None:
        """Get result from Django-Q."""
        try:
            from django_q.models import Task
        except ImportError:
            return None

        try:
            task = Task.objects.get(id=task_id)

            if task.success is None:
                status = "running"
            elif task.success:
                status = "completed"
            else:
                status = "failed"

            return TaskResult(
                task_id=task_id,
                status=status,
                result=task.result,
            )
        except Task.DoesNotExist:
            return TaskResult(task_id=task_id, status="pending")


# Global task executor
_task_backend: BaseTaskBackend | None = None


def get_task_backend() -> BaseTaskBackend:
    """Get the configured task backend."""
    global _task_backend

    if _task_backend is None:
        from swiftapi.conf import import_from_string, settings

        backend_path = getattr(settings, "TASK_BACKEND", None)

        if backend_path:
            backend_class = import_from_string(backend_path, "TASK_BACKEND")
            _task_backend = backend_class()
        else:
            # Default to async backend
            _task_backend = AsyncTaskBackend()

    return _task_backend


def background_task(func: Callable) -> Callable:
    """
    Decorator to run a function as a background task.

    Usage:
        @background_task
        async def send_email(user_id: int, subject: str):
            user = await User.objects.aget(pk=user_id)
            # Send email...

        # Call triggers background execution
        result = send_email.delay(user.id, "Welcome!")
        print(result.task_id)
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Direct call runs synchronously
        if asyncio.iscoroutinefunction(func):
            return asyncio.run(func(*args, **kwargs))
        return func(*args, **kwargs)

    def delay(*args: Any, **kwargs: Any) -> TaskResult:
        """Queue for background execution."""
        backend = get_task_backend()
        return backend.delay(func, *args, **kwargs)

    wrapper.delay = delay  # type: ignore
    wrapper.original = func  # type: ignore

    return wrapper


def after_response(func: Callable) -> Callable:
    """
    Decorator to run a function after the response is sent.

    The function runs in the background after the HTTP response.

    Usage:
        class UserViewSet(ViewSet):
            @after_response
            async def log_activity(self, user, action):
                await ActivityLog.objects.acreate(user=user, action=action)

            async def create(self, request):
                user = await super().create(request)
                self.log_activity(user, "created")  # Runs after response
                return user
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        backend = get_task_backend()
        backend.delay(func, *args, **kwargs)

    return wrapper


# Task status endpoint helper
def get_task_status_view():
    """
    Create a view for checking task status.

    Usage:
        urlpatterns = [
            path("api/tasks/<str:task_id>/", get_task_status_view()),
        ]
    """
    from django.http import JsonResponse

    def task_status_view(request, task_id: str) -> JsonResponse:
        backend = get_task_backend()
        result = backend.get_result(task_id)

        if result is None:
            return JsonResponse(
                {"error": {"code": "not_found", "message": "Task not found"}},
                status=404,
            )

        return JsonResponse({"data": result.to_dict()})

    return task_status_view
