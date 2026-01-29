"""
SwiftAPI Metadata.

OPTIONS response handling for API schema information - similar to DRF's metadata.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.http import HttpRequest, JsonResponse

if TYPE_CHECKING:
    from swiftapi.viewsets import ViewSet


class BaseMetadata:
    """
    Base class for metadata handlers.

    Metadata handlers determine what information is returned in OPTIONS responses.
    """

    def determine_metadata(self, request: HttpRequest, view: ViewSet) -> dict[str, Any]:
        """Return metadata for the given request and view."""
        raise NotImplementedError()


class SimpleMetadata(BaseMetadata):
    """
    Simple metadata handler that returns basic information.

    Example OPTIONS response:
        {
            "name": "User List",
            "description": "List all users",
            "renders": ["application/json"],
            "parses": ["application/json"],
            "actions": {
                "POST": {
                    "email": {
                        "type": "email",
                        "required": true,
                        "label": "Email",
                        "max_length": 254
                    }
                }
            }
        }
    """

    label_lookup = {
        "CharField": "string",
        "TextField": "string",
        "EmailField": "email",
        "URLField": "url",
        "SlugField": "slug",
        "RegexField": "regex",
        "UUIDField": "uuid",
        "IPAddressField": "ip",
        "IntegerField": "integer",
        "FloatField": "float",
        "DecimalField": "decimal",
        "BooleanField": "boolean",
        "NullBooleanField": "boolean",
        "DateTimeField": "datetime",
        "DateField": "date",
        "TimeField": "time",
        "DurationField": "duration",
        "ChoiceField": "choice",
        "MultipleChoiceField": "multiple choice",
        "FileField": "file upload",
        "ImageField": "image upload",
        "ListField": "list",
        "DictField": "nested object",
        "JSONField": "json",
        "PrimaryKeyRelatedField": "field",
        "SlugRelatedField": "field",
        "HyperlinkedRelatedField": "url",
    }

    def determine_metadata(self, request: HttpRequest, view: ViewSet) -> dict[str, Any]:
        """Return metadata for the view."""
        return {
            "name": self.get_name(view),
            "description": self.get_description(view),
            "renders": self.get_renders(view),
            "parses": self.get_parses(view),
            "actions": self.get_actions(request, view),
        }

    def get_name(self, view: ViewSet) -> str:
        """Get view name."""
        if hasattr(view, "get_view_name"):
            return view.get_view_name()
        return view.__class__.__name__

    def get_description(self, view: ViewSet) -> str:
        """Get view description."""
        if hasattr(view, "get_view_description"):
            return view.get_view_description()
        return view.__class__.__doc__ or ""

    def get_renders(self, view: ViewSet) -> list[str]:
        """Get supported render formats."""
        return ["application/json"]

    def get_parses(self, view: ViewSet) -> list[str]:
        """Get supported parse formats."""
        return ["application/json", "multipart/form-data"]

    def get_actions(self, request: HttpRequest, view: ViewSet) -> dict[str, Any]:
        """Get available actions with their field schemas."""
        actions = {}

        # Check for write operations
        if hasattr(view, "create"):
            actions["POST"] = self.get_schema_info(view, "write")

        if hasattr(view, "update"):
            actions["PUT"] = self.get_schema_info(view, "write")

        if hasattr(view, "partial_update"):
            actions["PATCH"] = self.get_schema_info(view, "write")

        return actions

    def get_schema_info(self, view: ViewSet, schema_type: str = "write") -> dict[str, Any]:
        """Get field information from schema."""
        schema_class = getattr(view, f"{schema_type}_schema", None)
        if schema_class is None:
            schema_class = getattr(view, "read_schema", None)

        if schema_class is None:
            return {}

        field_info = {}

        # Get fields from schema annotations
        if hasattr(schema_class, "__annotations__"):
            for field_name, field_type in schema_class.__annotations__.items():
                if field_name.startswith("_"):
                    continue

                field_info[field_name] = {
                    "type": self._get_type_name(field_type),
                    "required": True,  # Default, could be refined
                }

        return field_info

    def _get_type_name(self, field_type: Any) -> str:
        """Get human-readable type name."""
        type_name = str(field_type)

        # Handle Optional types
        if "Optional" in type_name:
            type_name = type_name.replace("Optional[", "").rstrip("]")

        # Map Python types to field types
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "datetime": "datetime",
            "date": "date",
            "time": "time",
            "uuid.UUID": "uuid",
            "Decimal": "decimal",
        }

        for py_type, field_type in type_map.items():
            if py_type in type_name:
                return field_type

        return "field"


class MinimalMetadata(BaseMetadata):
    """
    Minimal metadata handler that only returns basic information.

    Use this for production APIs where schema exposure is not desired.
    """

    def determine_metadata(self, request: HttpRequest, view: ViewSet) -> dict[str, Any]:
        return {
            "name": view.__class__.__name__,
        }


def get_options_response(request: HttpRequest, view: ViewSet) -> JsonResponse:
    """
    Generate OPTIONS response for a view.

    Usage in ViewSet:
        async def options(self, request, *args, **kwargs):
            return get_options_response(request, self)
    """
    from swiftapi.conf import settings

    # Get metadata class from settings or use default
    metadata_class_path = getattr(settings, "DEFAULT_METADATA_CLASS", None)
    if metadata_class_path:
        from swiftapi.conf import import_string
        metadata_class = import_string(metadata_class_path)
    else:
        metadata_class = SimpleMetadata

    metadata = metadata_class().determine_metadata(request, view)

    response = JsonResponse(metadata)

    # Add Allow header with supported methods
    methods = []
    method_map = {
        "list": "GET",
        "retrieve": "GET",
        "create": "POST",
        "update": "PUT",
        "partial_update": "PATCH",
        "destroy": "DELETE",
    }

    for action, method in method_map.items():
        if hasattr(view, action) and method not in methods:
            methods.append(method)

    methods.append("OPTIONS")
    response["Allow"] = ", ".join(methods)

    return response


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BaseMetadata",
    "MinimalMetadata",
    "SimpleMetadata",
    "get_options_response",
]
