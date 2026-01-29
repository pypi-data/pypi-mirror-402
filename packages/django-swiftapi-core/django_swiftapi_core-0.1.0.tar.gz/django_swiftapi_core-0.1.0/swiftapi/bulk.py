"""
SwiftAPI Bulk Operations.

Support for bulk create, update, and delete operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction

from swiftapi.exceptions import ValidationError

if TYPE_CHECKING:
    from django.http import HttpRequest
    pass


class BulkMixin:
    """
    Mixin for ViewSets to add bulk operation support.

    Provides:
    - POST /resource/bulk/ - bulk create
    - PUT /resource/bulk/ - bulk update
    - DELETE /resource/bulk/ - bulk delete

    Usage:
        class UserViewSet(BulkMixin, ViewSet):
            model = User
            read_schema = UserSchema
            write_schema = UserWriteSchema
    """

    # Configuration
    bulk_max_items: int = 100
    bulk_all_or_nothing: bool = True  # Rollback on any failure

    async def bulk_create(
        self,
        request: HttpRequest,
    ) -> list[Any]:
        """
        Bulk create objects.

        POST /resource/bulk/
        Body: {"items": [{...}, {...}, ...]}

        Returns list of created objects.
        """
        items = await self._parse_bulk_items(request)

        if len(items) > self.bulk_max_items:
            raise ValidationError(
                f"Maximum {self.bulk_max_items} items allowed per request."
            )

        results = []
        errors = []

        if self.bulk_all_or_nothing:
            # All-or-nothing mode with transaction
            async with transaction.atomic():
                for i, item in enumerate(items):
                    try:
                        validated = await self._validate_bulk_item(item)
                        obj = await self._create_object(validated)
                        results.append(obj)
                    except ValidationError as e:
                        raise ValidationError({f"items[{i}]": e.detail})
        else:
            # Partial success mode
            for i, item in enumerate(items):
                try:
                    validated = await self._validate_bulk_item(item)
                    obj = await self._create_object(validated)
                    results.append({"index": i, "success": True, "data": obj})
                except ValidationError as e:
                    errors.append({"index": i, "success": False, "errors": e.detail})
                except Exception as e:
                    errors.append({"index": i, "success": False, "errors": str(e)})

        if errors and not results:
            raise ValidationError({"items": errors})

        return results

    async def bulk_update(
        self,
        request: HttpRequest,
    ) -> list[Any]:
        """
        Bulk update objects.

        PUT /resource/bulk/
        Body: {"items": [{"id": 1, ...}, {"id": 2, ...}, ...]}

        Returns list of updated objects.
        """
        items = await self._parse_bulk_items(request)

        if len(items) > self.bulk_max_items:
            raise ValidationError(
                f"Maximum {self.bulk_max_items} items allowed per request."
            )

        results = []
        errors = []

        lookup_field = getattr(self, "lookup_field", "pk")

        if self.bulk_all_or_nothing:
            async with transaction.atomic():
                for i, item in enumerate(items):
                    obj_id = item.get(lookup_field) or item.get("id")
                    if not obj_id:
                        raise ValidationError(
                            {f"items[{i}]": f"'{lookup_field}' or 'id' is required."}
                        )

                    try:
                        obj = await self.get_object(obj_id)  # type: ignore
                        validated = await self._validate_bulk_item(item, partial=True)

                        for key, value in validated.items():
                            setattr(obj, key, value)

                        await obj.asave()
                        results.append(obj)
                    except ValidationError as e:
                        raise ValidationError({f"items[{i}]": e.detail})
        else:
            for i, item in enumerate(items):
                obj_id = item.get(lookup_field) or item.get("id")
                if not obj_id:
                    errors.append({
                        "index": i,
                        "success": False,
                        "errors": f"'{lookup_field}' or 'id' is required.",
                    })
                    continue

                try:
                    obj = await self.get_object(obj_id)  # type: ignore
                    validated = await self._validate_bulk_item(item, partial=True)

                    for key, value in validated.items():
                        setattr(obj, key, value)

                    await obj.asave()
                    results.append({"index": i, "success": True, "data": obj})
                except Exception as e:
                    errors.append({"index": i, "success": False, "errors": str(e)})

        if errors and not results:
            raise ValidationError({"items": errors})

        return results

    async def bulk_delete(
        self,
        request: HttpRequest,
    ) -> dict[str, Any]:
        """
        Bulk delete objects.

        DELETE /resource/bulk/
        Body: {"ids": [1, 2, 3, ...]}

        Returns count of deleted objects.
        """
        import json

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON body.")

        ids = body.get("ids", [])

        if not isinstance(ids, list):
            raise ValidationError("'ids' must be a list.")

        if len(ids) > self.bulk_max_items:
            raise ValidationError(
                f"Maximum {self.bulk_max_items} items allowed per request."
            )

        lookup_field = getattr(self, "lookup_field", "pk")
        queryset = self.get_filtered_queryset()  # type: ignore

        if self.bulk_all_or_nothing:
            async with transaction.atomic():
                deleted = await queryset.filter(
                    **{f"{lookup_field}__in": ids}
                ).adelete()
        else:
            deleted = await queryset.filter(
                **{f"{lookup_field}__in": ids}
            ).adelete()

        return {"deleted": deleted[0]}

    async def _parse_bulk_items(self, request: HttpRequest) -> list[dict]:
        """Parse items from request body."""
        import json

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON body.")

        items = body.get("items", [])

        if not isinstance(items, list):
            raise ValidationError("'items' must be a list.")

        return items

    async def _validate_bulk_item(
        self,
        item: dict,
        partial: bool = False,
    ) -> dict[str, Any]:
        """Validate a single item using write_schema."""
        write_schema = getattr(self, "write_schema", None)

        if write_schema:
            return write_schema.validate(item, partial=partial)

        return item

    async def _create_object(self, data: dict) -> Any:
        """Create a single object."""
        model = self.model

        # Add tenant if configured
        tenant_field = getattr(self, "tenant_field", None)
        if tenant_field and hasattr(self, "request"):
            request = self.request
            if hasattr(request, "tenant"):
                data[tenant_field] = request.tenant

        return await model.objects.acreate(**data)


class BulkRouter:
    """
    Router mixin that adds bulk endpoints for ViewSets with BulkMixin.
    """

    def get_bulk_urls(self, prefix: str, viewset: type, basename: str):
        """Generate bulk operation URLs."""
        from django.urls import re_path

        from swiftapi.handlers import create_handler

        urls = []

        if hasattr(viewset, "bulk_create"):
            urls.append(
                re_path(
                    rf"^{prefix}/bulk/$",
                    create_handler(viewset, {"post": "bulk_create"}, {}),
                    name=f"{basename}-bulk-create",
                )
            )

        if hasattr(viewset, "bulk_update"):
            urls.append(
                re_path(
                    rf"^{prefix}/bulk/$",
                    create_handler(viewset, {"put": "bulk_update"}, {}),
                    name=f"{basename}-bulk-update",
                )
            )

        if hasattr(viewset, "bulk_delete"):
            urls.append(
                re_path(
                    rf"^{prefix}/bulk/$",
                    create_handler(viewset, {"delete": "bulk_delete"}, {}),
                    name=f"{basename}-bulk-delete",
                )
            )

        return urls
