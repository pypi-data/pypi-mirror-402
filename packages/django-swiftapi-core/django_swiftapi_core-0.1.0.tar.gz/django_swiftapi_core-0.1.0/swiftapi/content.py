"""
SwiftAPI Content Negotiation.

Support for multiple content types (JSON, CSV, XML, etc.)
"""

from __future__ import annotations

import csv
import io
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse


class ContentNegotiator:
    """
    Handles content type negotiation for requests and responses.

    Determines the best content type based on:
    1. Accept header
    2. Format query parameter (?format=csv)
    3. URL suffix (.json, .csv)
    """

    default_format = "json"
    format_param = "format"

    def __init__(
        self,
        renderers: list | None = None,
        parsers: list | None = None,
    ) -> None:
        """
        Initialize negotiator.

        Args:
            renderers: List of renderer classes
            parsers: List of parser classes
        """
        self.renderers = renderers or [JSONRenderer]
        self.parsers = parsers or [JSONParser]

    def select_renderer(
        self,
        request: HttpRequest,
        strict: bool = False,
    ) -> tuple[type, str]:
        """
        Select the best renderer for the request.

        Args:
            request: HTTP request
            strict: If True, return None when no match (for 406 response)

        Returns:
            Tuple of (renderer_class, media_type)
        """
        # Check format query param
        format_param = request.GET.get(self.format_param)
        if format_param:
            for renderer in self.renderers:
                if renderer.format == format_param:
                    return renderer, renderer.media_type
            if strict:
                return None, None  # type: ignore

        # Check Accept header
        accept = request.META.get("HTTP_ACCEPT", "*/*")

        for renderer in self.renderers:
            if self._matches_accept(renderer.media_type, accept):
                return renderer, renderer.media_type

        # No match found
        if strict and accept != "*/*":
            return None, None  # type: ignore

        # Default to first renderer
        return self.renderers[0], self.renderers[0].media_type

    def select_parser(
        self,
        request: HttpRequest,
    ) -> type:
        """
        Select the best parser for the request.

        Returns:
            Parser class
        """
        content_type = request.content_type or "application/json"

        for parser in self.parsers:
            if parser.media_type in content_type:
                return parser

        return self.parsers[0]

    def _matches_accept(self, media_type: str, accept: str) -> bool:
        """Check if media type matches Accept header."""
        accept_types = [a.strip().split(";")[0] for a in accept.split(",")]

        if "*/*" in accept_types:
            return True

        if media_type in accept_types:
            return True

        # Check type wildcard (e.g., application/*)
        type_part = media_type.split("/")[0]
        return f"{type_part}/*" in accept_types


# Renderers

class BaseRenderer:
    """Base class for response renderers."""

    media_type = "application/octet-stream"
    format = ""
    charset = "utf-8"

    def render(self, data: Any) -> bytes:
        """Render data to bytes."""
        raise NotImplementedError

    def get_response(
        self,
        data: Any,
        status: int = 200,
        headers: dict | None = None,
    ) -> HttpResponse:
        """Create HTTP response with rendered data."""
        content = self.render(data)

        response = HttpResponse(
            content,
            content_type=f"{self.media_type}; charset={self.charset}",
            status=status,
        )

        if headers:
            for key, value in headers.items():
                response[key] = value

        return response


class JSONRenderer(BaseRenderer):
    """JSON response renderer."""

    media_type = "application/json"
    format = "json"

    def render(self, data: Any) -> bytes:
        import json
        return json.dumps(
            data,
            ensure_ascii=False,
            default=str,
        ).encode(self.charset)

    def get_response(
        self,
        data: Any,
        status: int = 200,
        headers: dict | None = None,
    ) -> JsonResponse:
        response = JsonResponse(data, status=status, safe=False)

        if headers:
            for key, value in headers.items():
                response[key] = value

        return response


class CSVRenderer(BaseRenderer):
    """CSV response renderer for list data."""

    media_type = "text/csv"
    format = "csv"

    def render(self, data: Any) -> bytes:
        output = io.StringIO()

        # Handle wrapped data
        if isinstance(data, dict):
            items = data.get("results") or data.get("data") or []
        elif isinstance(data, list):
            items = data
        else:
            items = [data]

        if not items:
            return b""

        # Get headers from first item
        if isinstance(items[0], dict):
            headers = list(items[0].keys())
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            writer.writerows(items)
        else:
            # Assume objects with __dict__
            headers = [k for k in dir(items[0]) if not k.startswith("_")]
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            for item in items:
                writer.writerow({k: getattr(item, k, "") for k in headers})

        return output.getvalue().encode(self.charset)

    def get_response(
        self,
        data: Any,
        status: int = 200,
        headers: dict | None = None,
    ) -> HttpResponse:
        response = super().get_response(data, status, headers)
        response["Content-Disposition"] = 'attachment; filename="export.csv"'
        return response


class XMLRenderer(BaseRenderer):
    """XML response renderer."""

    media_type = "application/xml"
    format = "xml"

    def render(self, data: Any) -> bytes:
        output = ['<?xml version="1.0" encoding="UTF-8"?>']
        output.append(self._to_xml(data, "response"))
        return "\n".join(output).encode(self.charset)

    def _to_xml(self, data: Any, tag: str) -> str:
        """Convert data to XML string."""
        if data is None:
            return f"<{tag}/>"

        if isinstance(data, dict):
            children = "".join(
                self._to_xml(v, k) for k, v in data.items()
            )
            return f"<{tag}>{children}</{tag}>"

        if isinstance(data, list):
            item_tag = tag.rstrip("s") if tag.endswith("s") else "item"
            children = "".join(
                self._to_xml(item, item_tag) for item in data
            )
            return f"<{tag}>{children}</{tag}>"

        # Escape special characters
        value = str(data)
        value = value.replace("&", "&amp;")
        value = value.replace("<", "&lt;")
        value = value.replace(">", "&gt;")

        return f"<{tag}>{value}</{tag}>"


class HTMLRenderer(BaseRenderer):
    """HTML response renderer for browsable API."""

    media_type = "text/html"
    format = "html"

    def render(self, data: Any) -> bytes:
        import json

        json_data = json.dumps(data, indent=2, default=str)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>API Response</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; }}
        pre {{ background: #f5f5f5; padding: 1rem; border-radius: 4px; overflow: auto; }}
        .status {{ color: #28a745; }}
    </style>
</head>
<body>
    <h1>API Response</h1>
    <p class="status">200 OK</p>
    <pre>{json_data}</pre>
</body>
</html>
        """

        return html.encode(self.charset)


# Parsers

class BaseParser:
    """Base class for request parsers."""

    media_type = "application/octet-stream"

    def parse(self, stream: bytes) -> Any:
        """Parse request body."""
        raise NotImplementedError


class JSONParser(BaseParser):
    """JSON request parser."""

    media_type = "application/json"

    def parse(self, stream: bytes) -> Any:
        import json

        if not stream:
            return {}

        return json.loads(stream.decode("utf-8"))


class FormParser(BaseParser):
    """Form data request parser."""

    media_type = "application/x-www-form-urlencoded"

    def parse(self, stream: bytes) -> dict[str, Any]:
        from urllib.parse import parse_qs

        data = parse_qs(stream.decode("utf-8"))
        return {k: v[0] if len(v) == 1 else v for k, v in data.items()}


# Content type middleware

class ContentNegotiationMiddleware:
    """
    Django middleware for content negotiation.

    Add to MIDDLEWARE:
        "swiftapi.content.ContentNegotiationMiddleware"
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.negotiator = ContentNegotiator(
            renderers=[JSONRenderer, CSVRenderer, XMLRenderer, HTMLRenderer],
            parsers=[JSONParser, FormParser],
        )

    def __call__(self, request: HttpRequest):
        # Select parser and renderer
        renderer_class, media_type = self.negotiator.select_renderer(request)
        parser_class = self.negotiator.select_parser(request)

        # Attach to request
        request.accepted_renderer = renderer_class()  # type: ignore
        request.accepted_media_type = media_type  # type: ignore
        request.parser = parser_class()  # type: ignore

        response = self.get_response(request)

        return response
