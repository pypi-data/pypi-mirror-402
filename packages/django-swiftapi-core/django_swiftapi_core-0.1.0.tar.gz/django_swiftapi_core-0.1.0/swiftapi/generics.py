"""
SwiftAPI Generic Views.

Class-based views for common patterns - similar to DRF's generics.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from swiftapi.viewsets import GenericViewSet

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest


# =============================================================================
# Mixins (moved to separate mixins.py but included here for convenience)
# =============================================================================

class CreateModelMixin:
    """Mixin for create functionality."""

    async def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Create a new model instance."""
        from swiftapi.responses import CreatedResponse

        data = await self.get_request_data(request)
        validated = self.write_schema.validate(data)

        instance = await self.perform_create(validated)

        output = self.read_schema.serialize(instance)
        return CreatedResponse(data=output)

    async def perform_create(self, validated_data: dict) -> Any:
        """Perform the actual creation."""
        return await self.model.objects.acreate(**validated_data)


class ListModelMixin:
    """Mixin for list functionality."""

    async def list(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """List all model instances."""
        from swiftapi.responses import SuccessResponse

        queryset = await self.get_queryset()
        queryset = await self.filter_queryset(queryset)

        # Paginate if needed
        if hasattr(self, "paginate_queryset"):
            page = await self.paginate_queryset(queryset)
            if page is not None:
                output = [self.read_schema.serialize(obj) for obj in page]
                return self.get_paginated_response(output)

        items = [obj async for obj in queryset]
        output = [self.read_schema.serialize(obj) for obj in items]
        return SuccessResponse(data=output)


class RetrieveModelMixin:
    """Mixin for retrieve functionality."""

    async def retrieve(self, request: HttpRequest, pk: Any, *args: Any, **kwargs: Any) -> Any:
        """Retrieve a single model instance."""
        from swiftapi.responses import SuccessResponse

        instance = await self.get_object(pk)
        output = self.read_schema.serialize(instance)
        return SuccessResponse(data=output)


class UpdateModelMixin:
    """Mixin for update functionality."""

    async def update(self, request: HttpRequest, pk: Any, *args: Any, **kwargs: Any) -> Any:
        """Update a model instance."""
        from swiftapi.responses import SuccessResponse

        instance = await self.get_object(pk)
        data = await self.get_request_data(request)
        validated = self.write_schema.validate(data)

        instance = await self.perform_update(instance, validated)

        output = self.read_schema.serialize(instance)
        return SuccessResponse(data=output)

    async def partial_update(self, request: HttpRequest, pk: Any, *args: Any, **kwargs: Any) -> Any:
        """Partially update a model instance."""
        from swiftapi.responses import SuccessResponse

        instance = await self.get_object(pk)
        data = await self.get_request_data(request)
        validated = self.write_schema.validate(data, partial=True)

        instance = await self.perform_update(instance, validated)

        output = self.read_schema.serialize(instance)
        return SuccessResponse(data=output)

    async def perform_update(self, instance: Any, validated_data: dict) -> Any:
        """Perform the actual update."""
        for key, value in validated_data.items():
            setattr(instance, key, value)
        await instance.asave()
        return instance


class DestroyModelMixin:
    """Mixin for delete functionality."""

    async def destroy(self, request: HttpRequest, pk: Any, *args: Any, **kwargs: Any) -> Any:
        """Delete a model instance."""
        from swiftapi.responses import NoContentResponse

        instance = await self.get_object(pk)
        await self.perform_destroy(instance)
        return NoContentResponse()

    async def perform_destroy(self, instance: Any) -> None:
        """Perform the actual deletion."""
        await instance.adelete()


# =============================================================================
# Generic API Views
# =============================================================================

class GenericAPIView(GenericViewSet):
    """
    Base class for all generic views.

    Provides common functionality for getting querysets and objects.
    """

    queryset = None
    read_schema = None
    write_schema = None
    lookup_field = "pk"
    lookup_url_kwarg = None
    pagination_class = None
    filter_backends = []

    async def get_queryset(self) -> QuerySet:
        """Get the queryset for this view."""
        if self.queryset is None:
            if self.model is not None:
                return self.model.objects.all()
            raise ValueError("No queryset or model defined")
        return self.queryset.all()

    async def get_object(self, pk: Any) -> Any:
        """Get a single object by primary key."""
        from swiftapi.exceptions import NotFound

        queryset = await self.get_queryset()

        try:
            return await queryset.aget(**{self.lookup_field: pk})
        except self.model.DoesNotExist:
            raise NotFound()

    async def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply filters to the queryset."""
        for backend in self.filter_backends:
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    async def get_request_data(self, request: HttpRequest) -> dict:
        """Get request data."""
        if hasattr(request, "data"):
            return request.data
        import json
        try:
            return json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, ValueError):
            return {}


# =============================================================================
# Concrete View Classes
# =============================================================================

class CreateAPIView(CreateModelMixin, GenericAPIView):
    """
    Concrete view for creating a model instance.

    Example:
        class UserCreateView(CreateAPIView):
            model = User
            write_schema = UserCreateSchema
            read_schema = UserSchema
    """
    pass


class ListAPIView(ListModelMixin, GenericAPIView):
    """
    Concrete view for listing model instances.

    Example:
        class UserListView(ListAPIView):
            model = User
            read_schema = UserSchema
    """
    pass


class RetrieveAPIView(RetrieveModelMixin, GenericAPIView):
    """
    Concrete view for retrieving a model instance.

    Example:
        class UserDetailView(RetrieveAPIView):
            model = User
            read_schema = UserSchema
    """
    pass


class DestroyAPIView(DestroyModelMixin, GenericAPIView):
    """
    Concrete view for deleting a model instance.

    Example:
        class UserDeleteView(DestroyAPIView):
            model = User
    """
    pass


class UpdateAPIView(UpdateModelMixin, GenericAPIView):
    """
    Concrete view for updating a model instance.

    Example:
        class UserUpdateView(UpdateAPIView):
            model = User
            write_schema = UserUpdateSchema
            read_schema = UserSchema
    """
    pass


class ListCreateAPIView(ListModelMixin, CreateModelMixin, GenericAPIView):
    """
    Concrete view for listing and creating model instances.

    Example:
        class UserListCreateView(ListCreateAPIView):
            model = User
            read_schema = UserSchema
            write_schema = UserCreateSchema
    """
    pass


class RetrieveUpdateAPIView(RetrieveModelMixin, UpdateModelMixin, GenericAPIView):
    """
    Concrete view for retrieving and updating a single model instance.

    Example:
        class UserRetrieveUpdateView(RetrieveUpdateAPIView):
            model = User
            read_schema = UserSchema
            write_schema = UserUpdateSchema
    """
    pass


class RetrieveDestroyAPIView(RetrieveModelMixin, DestroyModelMixin, GenericAPIView):
    """
    Concrete view for retrieving and deleting a single model instance.

    Example:
        class UserRetrieveDestroyView(RetrieveDestroyAPIView):
            model = User
            read_schema = UserSchema
    """
    pass


class RetrieveUpdateDestroyAPIView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    """
    Concrete view for retrieving, updating, and deleting a single model instance.

    Example:
        class UserDetailView(RetrieveUpdateDestroyAPIView):
            model = User
            read_schema = UserSchema
            write_schema = UserUpdateSchema
    """
    pass


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Concrete views
    "CreateAPIView",
    # Mixins
    "CreateModelMixin",
    "DestroyAPIView",
    "DestroyModelMixin",
    # Base
    "GenericAPIView",
    "ListAPIView",
    "ListCreateAPIView",
    "ListModelMixin",
    "RetrieveAPIView",
    "RetrieveDestroyAPIView",
    "RetrieveModelMixin",
    "RetrieveUpdateAPIView",
    "RetrieveUpdateDestroyAPIView",
    "UpdateAPIView",
    "UpdateModelMixin",
]
