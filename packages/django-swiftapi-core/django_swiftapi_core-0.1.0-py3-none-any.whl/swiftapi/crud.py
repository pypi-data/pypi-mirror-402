"""
SwiftAPI CRUD Generator.

Auto-generates ViewSets and Schemas from Django models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models import Model

    from swiftapi.permissions import BasePermission


def create_crud_viewset(
    model: type[Model],
    *,
    exclude: list[str] | None = None,
    read_only_fields: list[str] | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    tenant_field: str | None = None,
    queryset_filter: dict[str, Any] | None = None,
) -> type:
    """
    Create a complete CRUD ViewSet for a model.

    This is the zero-config CRUD generation feature that allows
    creating a full REST API from just a model.

    Args:
        model: Django model class
        exclude: Fields to exclude from schemas
        read_only_fields: Fields that are read-only
        permission_classes: Permissions for the ViewSet
        tenant_field: Field for multi-tenancy filtering
        queryset_filter: Additional queryset filters

    Returns:
        Generated ViewSet class

    Example:
        from swiftapi.crud import create_crud_viewset
        from myapp.models import Article

        ArticleViewSet = create_crud_viewset(
            Article,
            exclude=["internal_notes"],
            read_only_fields=["created_at", "updated_at"],
            permission_classes=[IsAuthenticated],
        )
    """
    from swiftapi.schemas import Schema
    from swiftapi.viewsets import ModelViewSet

    # Generate schemas from model
    exclude = exclude or []
    read_only_fields = read_only_fields or []

    # Read schema includes all non-excluded fields
    ReadSchema = Schema.from_model(
        model,
        fields="__all__",
        exclude=exclude,
        read_only_fields=read_only_fields,
    )

    # Write schema excludes read-only fields from input
    write_exclude = list(set(exclude + read_only_fields + ["id", "pk", "created_at", "updated_at"]))
    WriteSchema = Schema.from_model(
        model,
        fields="__all__",
        exclude=write_exclude,
    )

    # Create ViewSet class
    class GeneratedViewSet(ModelViewSet):
        pass

    GeneratedViewSet.model = model
    GeneratedViewSet.read_schema = ReadSchema
    GeneratedViewSet.write_schema = WriteSchema

    if permission_classes:
        GeneratedViewSet.permission_classes = permission_classes

    if tenant_field:
        GeneratedViewSet.tenant_field = tenant_field

    if queryset_filter:
        original_get_queryset = GeneratedViewSet.get_queryset

        def filtered_get_queryset(self):
            qs = original_get_queryset(self)
            return qs.filter(**queryset_filter)

        GeneratedViewSet.get_queryset = filtered_get_queryset

    # Set class name for debugging
    GeneratedViewSet.__name__ = f"{model.__name__}ViewSet"
    GeneratedViewSet.__qualname__ = f"{model.__name__}ViewSet"

    return GeneratedViewSet


def create_read_only_viewset(
    model: type[Model],
    *,
    exclude: list[str] | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
) -> type:
    """
    Create a read-only ViewSet for a model.

    Only provides list and retrieve actions.

    Args:
        model: Django model class
        exclude: Fields to exclude from schemas
        permission_classes: Permissions for the ViewSet

    Returns:
        Generated ReadOnlyViewSet class
    """
    from swiftapi.schemas import Schema
    from swiftapi.viewsets import ReadOnlyViewSet

    exclude = exclude or []

    ReadSchema = Schema.from_model(
        model,
        fields="__all__",
        exclude=exclude,
    )

    class GeneratedViewSet(ReadOnlyViewSet):
        pass

    GeneratedViewSet.model = model
    GeneratedViewSet.read_schema = ReadSchema

    if permission_classes:
        GeneratedViewSet.permission_classes = permission_classes

    GeneratedViewSet.__name__ = f"{model.__name__}ReadOnlyViewSet"
    GeneratedViewSet.__qualname__ = f"{model.__name__}ReadOnlyViewSet"

    return GeneratedViewSet


def model_to_schema(
    model: type[Model],
    *,
    fields: list[str] | str = "__all__",
    exclude: list[str] | None = None,
    read_only_fields: list[str] | None = None,
    name: str | None = None,
) -> type:
    """
    Create a Schema class from a Django model.

    Convenience function for generating schemas.

    Args:
        model: Django model class
        fields: Fields to include ("__all__" for all)
        exclude: Fields to exclude
        read_only_fields: Fields that are read-only
        name: Custom schema name

    Returns:
        Generated Schema class
    """
    from swiftapi.schemas import Schema

    schema = Schema.from_model(
        model,
        fields=fields,  # type: ignore
        exclude=exclude,
        read_only_fields=read_only_fields,
    )

    if name:
        schema.__name__ = name
        schema.__qualname__ = name

    return schema
