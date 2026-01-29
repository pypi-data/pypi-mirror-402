"""
SwiftAPI OpenAPI Documentation Generation.

Auto-generates OpenAPI 3.0 specs from schemas and viewsets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_args, get_origin

from django.http import HttpRequest, JsonResponse

if TYPE_CHECKING:
    from swiftapi.schemas import Schema
    from swiftapi.viewsets import ViewSet


class OpenAPIGenerator:
    """
    Generate OpenAPI 3.0 specification from SwiftAPI router.

    Automatically documents:
    - Endpoints and HTTP methods
    - Request/response schemas
    - Authentication requirements
    - Query parameters (filtering, pagination)

    Usage:
        from swiftapi.openapi import OpenAPIGenerator

        generator = OpenAPIGenerator(
            title="My API",
            version="1.0.0",
            description="API documentation",
        )

        schema = generator.generate(router)
    """

    def __init__(
        self,
        title: str = "API",
        version: str = "1.0.0",
        description: str = "",
        servers: list[dict] | None = None,
        security_schemes: dict | None = None,
    ) -> None:
        """
        Initialize the generator.

        Args:
            title: API title
            version: API version
            description: API description
            servers: List of server URLs
            security_schemes: Security scheme definitions
        """
        from swiftapi.conf import settings

        self.title = title or settings.SCHEMA_TITLE
        self.version = version or settings.SCHEMA_VERSION
        self.description = description or settings.SCHEMA_DESCRIPTION
        self.servers = servers or []
        self.security_schemes = security_schemes or {}

    def generate(self, router) -> dict[str, Any]:
        """
        Generate OpenAPI schema from router.

        Args:
            router: SwiftAPI Router instance

        Returns:
            OpenAPI 3.0 schema dictionary
        """
        schema: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": self._get_security_schemes(),
            },
        }

        if self.servers:
            schema["servers"] = self.servers

        # Generate paths from router
        for prefix, viewset_class, basename in router._registry:
            self._add_viewset_paths(schema, prefix, viewset_class, basename)

        return schema

    def _get_security_schemes(self) -> dict[str, Any]:
        """Get security scheme definitions."""
        schemes = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
            "sessionAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "sessionid",
            },
            "tokenAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Token authentication. Value: 'Token <your-token>'",
            },
        }
        schemes.update(self.security_schemes)
        return schemes

    def _add_viewset_paths(
        self,
        schema: dict,
        prefix: str,
        viewset_class: type[ViewSet],
        basename: str,
    ) -> None:
        """Add paths for a ViewSet."""
        # List/Create endpoint
        list_path = f"/{prefix}/"
        if list_path not in schema["paths"]:
            schema["paths"][list_path] = {}

        # List operation (GET)
        if hasattr(viewset_class, "list"):
            schema["paths"][list_path]["get"] = self._build_list_operation(
                viewset_class, basename
            )

        # Create operation (POST)
        if hasattr(viewset_class, "create"):
            schema["paths"][list_path]["post"] = self._build_create_operation(
                viewset_class, basename
            )

        # Detail endpoint
        detail_path = f"/{prefix}/{{id}}/"
        if detail_path not in schema["paths"]:
            schema["paths"][detail_path] = {}

        # Path parameters for detail endpoints
        path_params = [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": f"{basename} ID",
            }
        ]

        # Retrieve operation (GET)
        if hasattr(viewset_class, "retrieve"):
            op = self._build_retrieve_operation(viewset_class, basename)
            op["parameters"] = path_params + op.get("parameters", [])
            schema["paths"][detail_path]["get"] = op

        # Update operation (PUT)
        if hasattr(viewset_class, "update"):
            op = self._build_update_operation(viewset_class, basename)
            op["parameters"] = path_params + op.get("parameters", [])
            schema["paths"][detail_path]["put"] = op

        # Partial update operation (PATCH)
        if hasattr(viewset_class, "partial_update"):
            op = self._build_partial_update_operation(viewset_class, basename)
            op["parameters"] = path_params + op.get("parameters", [])
            schema["paths"][detail_path]["patch"] = op

        # Delete operation (DELETE)
        if hasattr(viewset_class, "destroy"):
            op = self._build_delete_operation(viewset_class, basename)
            op["parameters"] = path_params + op.get("parameters", [])
            schema["paths"][detail_path]["delete"] = op

        # Custom actions
        custom_actions = getattr(viewset_class, "_custom_actions", {})
        for action_name, config in custom_actions.items():
            self._add_custom_action_path(
                schema, prefix, viewset_class, basename, action_name, config
            )

        # Add schemas to components
        self._add_schema_components(schema, viewset_class)

    def _build_list_operation(
        self,
        viewset_class: type[ViewSet],
        basename: str,
    ) -> dict[str, Any]:
        """Build OpenAPI operation for list action."""
        read_schema = getattr(viewset_class, "read_schema", None)
        schema_name = f"{basename.title().replace('-', '')}Schema"

        operation: dict[str, Any] = {
            "summary": f"List {basename}",
            "operationId": f"list_{basename.replace('-', '_')}",
            "tags": [basename],
            "parameters": self._get_list_parameters(viewset_class),
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "count": {"type": "integer"},
                                    "next": {"type": "string", "nullable": True},
                                    "previous": {"type": "string", "nullable": True},
                                    "results": {
                                        "type": "array",
                                        "items": {"$ref": f"#/components/schemas/{schema_name}"}
                                        if read_schema
                                        else {},
                                    },
                                },
                            }
                        }
                    },
                }
            },
        }

        # Add security if permissions require auth
        if self._requires_auth(viewset_class):
            operation["security"] = [{"bearerAuth": []}, {"tokenAuth": []}]

        return operation

    def _build_create_operation(
        self,
        viewset_class: type[ViewSet],
        basename: str,
    ) -> dict[str, Any]:
        """Build OpenAPI operation for create action."""
        write_schema = getattr(viewset_class, "write_schema", None)
        read_schema = getattr(viewset_class, "read_schema", None)
        request_schema_name = f"{basename.title().replace('-', '')}CreateSchema"
        response_schema_name = f"{basename.title().replace('-', '')}Schema"

        operation: dict[str, Any] = {
            "summary": f"Create {basename}",
            "operationId": f"create_{basename.replace('-', '_')}",
            "tags": [basename],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{request_schema_name}"}
                        if write_schema
                        else {"type": "object"},
                    }
                },
            },
            "responses": {
                "201": {
                    "description": "Created",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{response_schema_name}"}
                            if read_schema
                            else {},
                        }
                    },
                },
                "400": {"description": "Validation error"},
            },
        }

        if self._requires_auth(viewset_class):
            operation["security"] = [{"bearerAuth": []}, {"tokenAuth": []}]

        return operation

    def _build_retrieve_operation(
        self,
        viewset_class: type[ViewSet],
        basename: str,
    ) -> dict[str, Any]:
        """Build OpenAPI operation for retrieve action."""
        read_schema = getattr(viewset_class, "read_schema", None)
        schema_name = f"{basename.title().replace('-', '')}Schema"

        operation: dict[str, Any] = {
            "summary": f"Get {basename}",
            "operationId": f"retrieve_{basename.replace('-', '_')}",
            "tags": [basename],
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                            if read_schema
                            else {},
                        }
                    },
                },
                "404": {"description": "Not found"},
            },
        }

        if self._requires_auth(viewset_class):
            operation["security"] = [{"bearerAuth": []}, {"tokenAuth": []}]

        return operation

    def _build_update_operation(
        self,
        viewset_class: type[ViewSet],
        basename: str,
    ) -> dict[str, Any]:
        """Build OpenAPI operation for update action."""
        write_schema = getattr(viewset_class, "write_schema", None)
        read_schema = getattr(viewset_class, "read_schema", None)
        request_schema_name = f"{basename.title().replace('-', '')}CreateSchema"
        response_schema_name = f"{basename.title().replace('-', '')}Schema"

        operation: dict[str, Any] = {
            "summary": f"Update {basename}",
            "operationId": f"update_{basename.replace('-', '_')}",
            "tags": [basename],
            "parameters": [],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{request_schema_name}"}
                        if write_schema
                        else {"type": "object"},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Updated",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{response_schema_name}"}
                            if read_schema
                            else {},
                        }
                    },
                },
                "404": {"description": "Not found"},
            },
        }

        if self._requires_auth(viewset_class):
            operation["security"] = [{"bearerAuth": []}, {"tokenAuth": []}]

        return operation

    def _build_partial_update_operation(
        self,
        viewset_class: type[ViewSet],
        basename: str,
    ) -> dict[str, Any]:
        """Build OpenAPI operation for partial update action."""
        op = self._build_update_operation(viewset_class, basename)
        op["summary"] = f"Partial update {basename}"
        op["operationId"] = f"partial_update_{basename.replace('-', '_')}"
        return op

    def _build_delete_operation(
        self,
        viewset_class: type[ViewSet],
        basename: str,
    ) -> dict[str, Any]:
        """Build OpenAPI operation for delete action."""
        operation: dict[str, Any] = {
            "summary": f"Delete {basename}",
            "operationId": f"delete_{basename.replace('-', '_')}",
            "tags": [basename],
            "parameters": [],
            "responses": {
                "204": {"description": "No content"},
                "404": {"description": "Not found"},
            },
        }

        if self._requires_auth(viewset_class):
            operation["security"] = [{"bearerAuth": []}, {"tokenAuth": []}]

        return operation

    def _add_custom_action_path(
        self,
        schema: dict,
        prefix: str,
        viewset_class: type[ViewSet],
        basename: str,
        action_name: str,
        config: dict,
    ) -> None:
        """Add path for a custom action."""
        detail = config.get("detail", True)
        url_path = config.get("url_path", action_name)
        methods = config.get("methods", ["GET"])

        path = f"/{prefix}/{{id}}/{url_path}/" if detail else f"/{prefix}/{url_path}/"

        if path not in schema["paths"]:
            schema["paths"][path] = {}

        for method in methods:
            method_lower = method.lower()
            operation: dict[str, Any] = {
                "summary": f"{action_name.replace('_', ' ').title()}",
                "operationId": f"{action_name}_{basename.replace('-', '_')}",
                "tags": [basename],
                "parameters": [],
                "responses": {
                    "200": {"description": "Successful response"},
                },
            }

            if detail:
                operation["parameters"].append({
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                })

            if self._requires_auth(viewset_class):
                operation["security"] = [{"bearerAuth": []}, {"tokenAuth": []}]

            schema["paths"][path][method_lower] = operation

    def _get_list_parameters(self, viewset_class: type[ViewSet]) -> list[dict]:
        """Get query parameters for list endpoint."""
        params = [
            {
                "name": "limit",
                "in": "query",
                "schema": {"type": "integer", "default": 25},
                "description": "Number of results to return",
            },
            {
                "name": "offset",
                "in": "query",
                "schema": {"type": "integer", "default": 0},
                "description": "Starting position",
            },
        ]

        # Add filter fields
        filter_fields = getattr(viewset_class, "filter_fields", [])
        for field in filter_fields:
            params.append({
                "name": field,
                "in": "query",
                "schema": {"type": "string"},
                "description": f"Filter by {field}",
            })

        # Add ordering
        ordering_fields = getattr(viewset_class, "ordering_fields", [])
        if ordering_fields:
            params.append({
                "name": "ordering",
                "in": "query",
                "schema": {"type": "string"},
                "description": f"Order by field. Prefix with - for descending. Options: {', '.join(ordering_fields)}",
            })

        # Add search
        search_fields = getattr(viewset_class, "search_fields", [])
        if search_fields:
            params.append({
                "name": "search",
                "in": "query",
                "schema": {"type": "string"},
                "description": "Search term",
            })

        return params

    def _requires_auth(self, viewset_class: type[ViewSet]) -> bool:
        """Check if ViewSet requires authentication."""
        permissions = getattr(viewset_class, "permission_classes", [])

        for perm in permissions:
            perm_name = perm.__name__ if isinstance(perm, type) else type(perm).__name__
            if "Authenticated" in perm_name or "Admin" in perm_name:
                return True

        return False

    def _add_schema_components(
        self,
        schema: dict,
        viewset_class: type[ViewSet],
    ) -> None:
        """Add schema components for ViewSet schemas."""
        read_schema = getattr(viewset_class, "read_schema", None)
        write_schema = getattr(viewset_class, "write_schema", None)

        if read_schema:
            name = read_schema.__name__
            if name not in schema["components"]["schemas"]:
                schema["components"]["schemas"][name] = self._schema_to_openapi(
                    read_schema
                )

        if write_schema:
            name = write_schema.__name__
            if name not in schema["components"]["schemas"]:
                schema["components"]["schemas"][name] = self._schema_to_openapi(
                    write_schema, for_write=True
                )

    def _schema_to_openapi(
        self,
        schema_class: type[Schema],
        for_write: bool = False,
    ) -> dict[str, Any]:
        """Convert SwiftAPI Schema to OpenAPI schema."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        fields = getattr(schema_class, "_fields", {})
        read_only_fields = getattr(schema_class, "_read_only_fields", set())
        write_only_fields = getattr(schema_class, "_write_only_fields", set())

        for field_name, (field_type, field_info) in fields.items():
            # Skip write-only fields in read schema
            if not for_write and field_name in write_only_fields:
                continue

            # Skip read-only fields in write schema
            if for_write and field_name in read_only_fields:
                continue

            prop = self._type_to_openapi(field_type)

            if field_info.description:
                prop["description"] = field_info.description

            if field_info.read_only:
                prop["readOnly"] = True

            if field_info.has_default():
                default = field_info.get_default()
                if default is not None and not callable(default):
                    prop["default"] = default

            properties[field_name] = prop

            if field_info.required and not field_info.has_default():
                required.append(field_name)

        result: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }

        if required:
            result["required"] = required

        return result

    def _type_to_openapi(self, python_type: Any) -> dict[str, Any]:
        """Convert Python type to OpenAPI type."""
        import datetime
        import uuid
        from decimal import Decimal

        origin = get_origin(python_type)

        # Handle Optional
        if origin is type(None) or (origin is type and python_type is type(None)):
            return {"type": "null"}

        # Handle Union (Optional)
        try:
            from typing import Union
            if origin is Union:
                args = get_args(python_type)
                non_none = [a for a in args if a is not type(None)]
                if len(non_none) == 1:
                    result = self._type_to_openapi(non_none[0])
                    result["nullable"] = True
                    return result
        except Exception:
            pass

        # Handle list
        if origin is list:
            args = get_args(python_type)
            return {
                "type": "array",
                "items": self._type_to_openapi(args[0]) if args else {},
            }

        # Handle dict
        if origin is dict:
            return {"type": "object"}

        # Basic types
        type_mapping = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            datetime.datetime: {"type": "string", "format": "date-time"},
            datetime.date: {"type": "string", "format": "date"},
            datetime.time: {"type": "string", "format": "time"},
            uuid.UUID: {"type": "string", "format": "uuid"},
            Decimal: {"type": "number"},
        }

        return type_mapping.get(python_type, {"type": "string"})


def get_openapi_view(router, **kwargs):
    """
    Create a view that returns the OpenAPI schema.

    Args:
        router: SwiftAPI Router instance
        **kwargs: Additional arguments for OpenAPIGenerator

    Returns:
        View function
    """
    generator = OpenAPIGenerator(**kwargs)

    def openapi_view(request: HttpRequest) -> JsonResponse:
        schema = generator.generate(router)
        return JsonResponse(schema, json_dumps_params={"indent": 2})

    return openapi_view


def get_swagger_ui_view(schema_url: str = "/api/schema/"):
    """
    Create a view that renders Swagger UI.

    Args:
        schema_url: URL to the OpenAPI schema endpoint

    Returns:
        View function
    """
    from django.http import HttpResponse

    def swagger_view(request: HttpRequest) -> HttpResponse:
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        html {{ box-sizing: border-box; overflow-y: scroll; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        body {{ margin: 0; background: #fafafa; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: "{schema_url}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            }});
        }};
    </script>
</body>
</html>
        """
        return HttpResponse(html, content_type="text/html")

    return swagger_view
