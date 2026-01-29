"""
SwiftAPI Response Classes.

Standardized response formatting and renderers.
"""

from __future__ import annotations

import json
from typing import Any

from django.http import HttpResponse, JsonResponse


class Response(JsonResponse):
    """
    Standard API response.

    Wraps data in a consistent format:
    - Success: {"data": ...}
    - Error: {"error": {...}}
    """

    def __init__(
        self,
        data: Any = None,
        status: int = 200,
        headers: dict | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Create a response.

        Args:
            data: Response data (will be wrapped in {"data": ...})
            status: HTTP status code
            headers: Additional response headers
            **kwargs: Additional arguments for JsonResponse
        """
        if status >= 400:
            # Error response
            response_data = data if isinstance(data, dict) and "error" in data else {"error": data}
        else:
            # Success response
            response_data = data if isinstance(data, dict) and "data" in data else {"data": data}

        super().__init__(response_data, status=status, **kwargs)

        if headers:
            for key, value in headers.items():
                self[key] = value


class SuccessResponse(Response):
    """Response for successful operations."""

    def __init__(
        self,
        data: Any = None,
        status: int = 200,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        response_data = {"data": data}
        if message:
            response_data["message"] = message
        super().__init__(data=response_data, status=status, **kwargs)


class CreatedResponse(Response):
    """Response for resource creation (201)."""

    def __init__(self, data: Any = None, **kwargs: Any) -> None:
        super().__init__(data=data, status=201, **kwargs)


class NoContentResponse(HttpResponse):
    """Response for successful deletion (204)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(status=204, **kwargs)


class ErrorResponse(Response):
    """Response for errors."""

    def __init__(
        self,
        message: str,
        code: str = "error",
        status: int = 400,
        field: str | None = None,
        details: Any = None,
        **kwargs: Any,
    ) -> None:
        error_data: dict[str, Any] = {
            "code": code,
            "message": message,
        }
        if field:
            error_data["field"] = field
        if details:
            error_data["details"] = details

        super().__init__(
            data={"error": error_data},
            status=status,
            **kwargs,
        )


class PaginatedResponse(Response):
    """Response for paginated list data."""

    def __init__(
        self,
        results: list,
        count: int,
        next_url: str | None = None,
        previous_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        data = {
            "count": count,
            "next": next_url,
            "previous": previous_url,
            "results": results,
        }
        super().__init__(data=data, **kwargs)


# Renderer classes for content negotiation

class BaseRenderer:
    """Base class for response renderers."""

    media_type = "application/octet-stream"
    format = ""

    def render(self, data: Any) -> bytes:
        """Render data to bytes."""
        raise NotImplementedError


class JSONRenderer(BaseRenderer):
    """Render responses as JSON."""

    media_type = "application/json"
    format = "json"

    def render(self, data: Any) -> bytes:
        """Render data to JSON bytes."""
        return json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")


class ORJSONRenderer(BaseRenderer):
    """
    Render responses using orjson for better performance.

    Requires: pip install orjson
    """

    media_type = "application/json"
    format = "json"

    def render(self, data: Any) -> bytes:
        """Render data using orjson."""
        try:
            import orjson
            return orjson.dumps(data)
        except ImportError:
            # Fall back to standard JSON
            return json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")


# Parser classes for request parsing

class BaseParser:
    """Base class for request parsers."""

    media_type = "application/octet-stream"

    def parse(self, stream: bytes) -> Any:
        """Parse request body."""
        raise NotImplementedError


class JSONParser(BaseParser):
    """Parse JSON request bodies."""

    media_type = "application/json"

    def parse(self, stream: bytes) -> Any:
        """Parse JSON bytes to Python object."""
        if not stream:
            return {}
        return json.loads(stream.decode("utf-8"))


class FormParser(BaseParser):
    """Parse form data request bodies."""

    media_type = "application/x-www-form-urlencoded"

    def parse(self, stream: bytes) -> dict[str, Any]:
        """Parse form data."""
        from urllib.parse import parse_qs

        data = parse_qs(stream.decode("utf-8"))
        # Convert single-item lists to values
        return {k: v[0] if len(v) == 1 else v for k, v in data.items()}


class MultiPartParser(BaseParser):
    """Parse multipart form data (file uploads)."""

    media_type = "multipart/form-data"

    def parse(self, stream: bytes) -> dict[str, Any]:
        """Parse multipart data."""
        # Django handles this automatically via request.POST/request.FILES
        raise NotImplementedError(
            "MultiPartParser should not be called directly. "
            "Use request.POST and request.FILES instead."
        )
