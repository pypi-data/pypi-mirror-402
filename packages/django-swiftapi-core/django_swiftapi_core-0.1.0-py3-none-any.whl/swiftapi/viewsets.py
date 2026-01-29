"""
SwiftAPI ViewSet System.

Async-first ViewSets with familiar DRF patterns for handling
CRUD operations with automatic schema validation.
"""

from __future__ import annotations

import asyncio
import functools
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    TypeVar,
)

from swiftapi.exceptions import MethodNotAllowed, NotFound, ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.models import Model, QuerySet
    from django.http import HttpRequest

    from swiftapi.permissions import BasePermission
    from swiftapi.schemas import Schema


T = TypeVar("T", bound="ViewSet")
ActionType = Literal["list", "create", "retrieve", "update", "partial_update", "destroy"]


class ViewSetMeta(type):
    """
    Metaclass for ViewSet that processes action methods and custom actions.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace)

        # Collect custom actions
        cls._custom_actions: dict[str, dict[str, Any]] = {}  # type: ignore

        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue
            attr = getattr(cls, attr_name, None)
            if callable(attr) and hasattr(attr, "_action_config"):
                cls._custom_actions[attr_name] = attr._action_config  # type: ignore

        return cls


def action(
    methods: list[str] | None = None,
    detail: bool = True,
    url_path: str | None = None,
    url_name: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    **kwargs: Any,
) -> Callable:
    """
    Decorator to mark a ViewSet method as a custom action.

    Args:
        methods: HTTP methods allowed (default ["GET"])
        detail: If True, requires an ID (e.g., /users/{id}/activate)
        url_path: Custom URL path (defaults to method name)
        url_name: Custom URL name
        permission_classes: Override permissions for this action
        **kwargs: Additional action configuration

    Example:
        class UserViewSet(ViewSet):
            @action(methods=["POST"], detail=True)
            async def activate(self, request, pk):
                user = await self.get_object(pk)
                user.is_active = True
                await user.asave()
                return {"status": "activated"}
    """
    if methods is None:
        methods = ["GET"]
    methods = [m.upper() for m in methods]

    def decorator(func: Callable) -> Callable:
        func._action_config = {  # type: ignore
            "methods": methods,
            "detail": detail,
            "url_path": url_path or func.__name__,
            "url_name": url_name,
            "permission_classes": permission_classes,
            **kwargs,
        }
        return func

    return decorator


class ViewSet(metaclass=ViewSetMeta):
    """
    Async-first ViewSet for handling CRUD operations.

    Provides familiar DRF-like patterns with native async support:
    - Async handler methods with sync fallback
    - Automatic schema validation for input/output
    - Permission class support
    - Queryset management

    Example:
        class UserViewSet(ViewSet):
            model = User
            read_schema = UserSchema
            write_schema = UserCreateSchema
            permissions = [IsAuthenticated]

            async def list(self, request):
                users = await self.get_queryset().aall()
                return users

            async def retrieve(self, request, pk):
                return await self.get_object(pk)

            async def create(self, request):
                data = await self.get_validated_data(request)
                user = await self.model.objects.acreate(**data)
                return user
    """

    # Model configuration
    model: ClassVar[type[Model] | None] = None
    queryset: ClassVar[QuerySet | None] = None

    # Schema configuration
    read_schema: ClassVar[type[Schema] | None] = None
    write_schema: ClassVar[type[Schema] | None] = None

    # Permission configuration
    permission_classes: ClassVar[list[type[BasePermission]]] = []

    # Multi-tenancy
    tenant_field: ClassVar[str | None] = None

    # Lookup field
    lookup_field: ClassVar[str] = "pk"
    lookup_url_kwarg: ClassVar[str | None] = None

    # Pagination
    pagination_class: ClassVar[type | None] = None

    # Filtering
    filter_fields: ClassVar[list[str]] = []
    ordering_fields: ClassVar[list[str]] = []
    search_fields: ClassVar[list[str]] = []

    # Custom actions registry
    _custom_actions: ClassVar[dict[str, dict[str, Any]]]

    # Instance attributes
    request: HttpRequest
    kwargs: dict[str, Any]
    action: str

    def __init__(
        self,
        request: HttpRequest | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the ViewSet.

        Args:
            request: The current HTTP request
            **kwargs: URL parameters (pk, etc.)
        """
        self.request = request  # type: ignore
        self.kwargs = kwargs
        self.action = ""

    def get_queryset(self) -> QuerySet:
        """
        Get the base queryset for this ViewSet.

        Override this method to customize queryset filtering.

        Returns:
            QuerySet for the model
        """
        if self.queryset is not None:
            return self.queryset.all()

        if self.model is not None:
            return self.model.objects.all()

        raise ValueError(
            f"{self.__class__.__name__} must define 'model' or 'queryset'"
        )

    def get_filtered_queryset(self) -> QuerySet:
        """
        Get queryset with tenant filtering applied.

        Returns:
            Filtered QuerySet
        """
        queryset = self.get_queryset()

        # Apply tenant filtering if configured
        if self.tenant_field and hasattr(self.request, "tenant"):
            tenant = getattr(self.request, "tenant", None)
            if tenant is not None:
                queryset = queryset.filter(**{self.tenant_field: tenant})

        return queryset

    async def get_object(self, pk: Any = None) -> Model:
        """
        Get a single object by primary key.

        Args:
            pk: Primary key value (uses URL kwargs if not provided)

        Returns:
            Model instance

        Raises:
            NotFound: If object doesn't exist
        """
        if pk is None:
            lookup_kwarg = self.lookup_url_kwarg or self.lookup_field
            pk = self.kwargs.get(lookup_kwarg)

        if pk is None:
            raise NotFound("No object identifier provided.")

        queryset = self.get_filtered_queryset()

        try:
            return await queryset.aget(**{self.lookup_field: pk})
        except self.model.DoesNotExist:  # type: ignore
            raise NotFound(f"{self.model.__name__} not found.")

    async def get_validated_data(
        self,
        request: HttpRequest | None = None,
        partial: bool = False,
    ) -> dict[str, Any]:
        """
        Parse and validate request body.

        Args:
            request: HTTP request (uses self.request if not provided)
            partial: If True, allows partial data (for PATCH)

        Returns:
            Validated data dictionary
        """
        request = request or self.request

        # Parse JSON body
        import json
        try:
            data = json.loads(request.body) if hasattr(request, "body") and request.body else {}
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")

        # Validate with schema
        if self.write_schema:
            return self.write_schema.validate(data, partial=partial)

        return data

    def serialize(
        self,
        instance: Any,
        many: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Serialize model instance(s) to dict.

        Args:
            instance: Model instance or queryset
            many: If True, serialize multiple instances

        Returns:
            Serialized data
        """
        if self.read_schema:
            return self.read_schema.serialize(instance, many=many)

        # Fallback: basic model to dict
        if many:
            return [self._model_to_dict(obj) for obj in instance]
        return self._model_to_dict(instance)

    def _model_to_dict(self, instance: Any) -> dict[str, Any]:
        """Convert a model instance to dictionary."""
        if isinstance(instance, dict):
            return instance

        if hasattr(instance, "__dict__"):
            result = {}
            for key, value in instance.__dict__.items():
                if not key.startswith("_"):
                    # Convert special types
                    if hasattr(value, "isoformat"):
                        value = value.isoformat()
                    elif hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        value = str(value)
                    result[key] = value
            return result

        return {"value": instance}

    # Default CRUD handlers

    async def list(self, request: HttpRequest) -> list[Any]:
        """
        List all objects.

        GET /resource/

        Returns:
            List of serialized objects
        """
        queryset = self.get_filtered_queryset()

        # Use async iteration
        objects = [obj async for obj in queryset]
        return objects

    async def retrieve(self, request: HttpRequest, pk: Any) -> Any:
        """
        Retrieve a single object.

        GET /resource/{pk}/

        Args:
            pk: Primary key of the object

        Returns:
            Serialized object
        """
        return await self.get_object(pk)

    async def create(self, request: HttpRequest) -> Any:
        """
        Create a new object.

        POST /resource/

        Returns:
            Created object
        """
        data = await self.get_validated_data(request)

        # Add tenant if configured
        if self.tenant_field and hasattr(request, "tenant"):
            data[self.tenant_field] = request.tenant

        obj = await self.model.objects.acreate(**data)  # type: ignore
        return obj

    async def update(self, request: HttpRequest, pk: Any) -> Any:
        """
        Update an existing object (full replacement).

        PUT /resource/{pk}/

        Args:
            pk: Primary key of the object

        Returns:
            Updated object
        """
        obj = await self.get_object(pk)
        data = await self.get_validated_data(request)

        for key, value in data.items():
            setattr(obj, key, value)

        await obj.asave()
        return obj

    async def partial_update(self, request: HttpRequest, pk: Any) -> Any:
        """
        Partially update an existing object.

        PATCH /resource/{pk}/

        Args:
            pk: Primary key of the object

        Returns:
            Updated object
        """
        obj = await self.get_object(pk)
        data = await self.get_validated_data(request, partial=True)

        for key, value in data.items():
            setattr(obj, key, value)

        await obj.asave()
        return obj

    async def destroy(self, request: HttpRequest, pk: Any) -> None:
        """
        Delete an object.

        DELETE /resource/{pk}/

        Args:
            pk: Primary key of the object
        """
        obj = await self.get_object(pk)
        await obj.adelete()


class GenericViewSet(ViewSet):
    """
    ViewSet with mixins for common operations.

    Use this as a base for customized ViewSets where you
    only want specific operations.
    """
    pass


class ReadOnlyViewSet(ViewSet):
    """
    ViewSet that only allows read operations.

    Only provides list and retrieve actions.
    """

    async def create(self, request: HttpRequest) -> Any:
        raise MethodNotAllowed("POST")

    async def update(self, request: HttpRequest, pk: Any) -> Any:
        raise MethodNotAllowed("PUT")

    async def partial_update(self, request: HttpRequest, pk: Any) -> Any:
        raise MethodNotAllowed("PATCH")

    async def destroy(self, request: HttpRequest, pk: Any) -> None:
        raise MethodNotAllowed("DELETE")


class ModelViewSet(ViewSet):
    """
    Full CRUD ViewSet for a model.

    Provides all standard CRUD operations:
    - list: GET /resource/
    - create: POST /resource/
    - retrieve: GET /resource/{pk}/
    - update: PUT /resource/{pk}/
    - partial_update: PATCH /resource/{pk}/
    - destroy: DELETE /resource/{pk}/
    """
    pass


def sync_to_async_view(func: Callable) -> Callable:
    """
    Wrap a sync view function to run in async context.

    Args:
        func: Sync function to wrap

    Returns:
        Async function
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(func, *args, **kwargs),
        )
    return wrapper


def is_async(func: Callable) -> bool:
    """Check if a function is async."""
    return asyncio.iscoroutinefunction(func) or asyncio.iscoroutinefunction(
        getattr(func, "__wrapped__", None)
    )
