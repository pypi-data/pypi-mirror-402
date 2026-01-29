"""
SwiftAPI Django Middleware.

Commonly needed middleware for API applications.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse, JsonResponse

from swiftapi.conf import settings
from swiftapi.exceptions import default_exception_handler

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger("swiftapi")


class RequestLoggingMiddleware:
    """
    Log all API requests and responses.

    Configuration:
        SWIFTAPI = {
            "ENABLE_REQUEST_LOGGING": True,
        }
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not settings.ENABLE_REQUEST_LOGGING:
            return self.get_response(request)

        start_time = time.perf_counter()
        request_id = self._get_request_id(request)

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "query": request.META.get("QUERY_STRING", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )

        response = self.get_response(request)

        # Log response
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[{request_id}] {response.status_code} ({duration_ms:.1f}ms)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Add timing header
        response["X-Response-Time"] = f"{duration_ms:.1f}ms"
        response[settings.REQUEST_ID_HEADER] = request_id

        return response

    def _get_request_id(self, request: HttpRequest) -> str:
        """Get or generate request ID."""
        header_name = "HTTP_" + settings.REQUEST_ID_HEADER.upper().replace("-", "_")
        request_id = request.META.get(header_name)

        if not request_id and settings.GENERATE_REQUEST_ID:
            request_id = str(uuid.uuid4())[:8]

        return request_id or ""


class ExceptionMiddleware:
    """
    Handle exceptions and return consistent JSON error responses.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            return self.handle_exception(request, exc)

    def handle_exception(
        self,
        request: HttpRequest,
        exc: Exception,
    ) -> JsonResponse:
        """Convert exception to JSON response."""
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                "path": request.path,
                "method": request.method,
            },
        )

        return default_exception_handler(exc, request)


class CORSMiddleware:
    """
    Handle CORS (Cross-Origin Resource Sharing) headers.

    Configuration:
        SWIFTAPI = {
            "CORS_ALLOWED_ORIGINS": ["http://localhost:3000"],
            "CORS_ALLOW_ALL_ORIGINS": False,
            "CORS_ALLOWED_METHODS": ["GET", "POST", "PUT", "PATCH", "DELETE"],
            "CORS_ALLOWED_HEADERS": ["*"],
            "CORS_ALLOW_CREDENTIALS": True,
            "CORS_MAX_AGE": 86400,
        }
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Handle preflight
        response = HttpResponse() if request.method == "OPTIONS" else self.get_response(request)

        self._add_cors_headers(request, response)
        return response

    def _add_cors_headers(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> None:
        """Add CORS headers to response."""
        origin = request.META.get("HTTP_ORIGIN", "")

        # Check if origin is allowed
        allow_all = getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False)
        allowed_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])

        if allow_all:
            response["Access-Control-Allow-Origin"] = "*"
        elif origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
        else:
            return  # Origin not allowed

        # Methods
        methods = getattr(
            settings,
            "CORS_ALLOWED_METHODS",
            ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        )
        response["Access-Control-Allow-Methods"] = ", ".join(methods)

        # Headers
        allowed_headers = getattr(settings, "CORS_ALLOWED_HEADERS", ["*"])
        if allowed_headers == ["*"]:
            # Reflect requested headers
            request_headers = request.META.get("HTTP_ACCESS_CONTROL_REQUEST_HEADERS", "")
            response["Access-Control-Allow-Headers"] = request_headers or "*"
        else:
            response["Access-Control-Allow-Headers"] = ", ".join(allowed_headers)

        # Credentials
        if getattr(settings, "CORS_ALLOW_CREDENTIALS", True):
            response["Access-Control-Allow-Credentials"] = "true"

        # Max age
        max_age = getattr(settings, "CORS_MAX_AGE", 86400)
        response["Access-Control-Max-Age"] = str(max_age)


class JSONBodyMiddleware:
    """
    Parse JSON request body and make it available as request.data.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        self._parse_json_body(request)
        return self.get_response(request)

    def _parse_json_body(self, request: HttpRequest) -> None:
        """Parse JSON body if present."""
        content_type = request.content_type or ""

        if "application/json" in content_type and request.body:
            try:
                request.data = json.loads(request.body)  # type: ignore
            except json.JSONDecodeError:
                request.data = {}  # type: ignore
        else:
            request.data = {}  # type: ignore


class CompressionMiddleware:
    """
    Compress responses using gzip.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Check if client accepts gzip
        accept_encoding = request.META.get("HTTP_ACCEPT_ENCODING", "")
        if "gzip" not in accept_encoding:
            return response

        # Skip if already compressed or too small
        if response.has_header("Content-Encoding"):
            return response

        content = response.content
        if len(content) < 200:  # Don't compress tiny responses
            return response

        # Compress
        import gzip
        compressed = gzip.compress(content)

        # Only use if smaller
        if len(compressed) < len(content):
            response.content = compressed
            response["Content-Encoding"] = "gzip"
            response["Content-Length"] = len(compressed)

        return response


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Prevent MIME-type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # XSS protection
        response["X-XSS-Protection"] = "1; mode=block"

        # Frame options
        response["X-Frame-Options"] = "DENY"

        # Referrer policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class RateLimitMiddleware:
    """
    Global rate limiting middleware.

    Configuration:
        SWIFTAPI = {
            "GLOBAL_RATE_LIMIT": "1000/minute",
        }
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        from swiftapi.throttling import SimpleRateThrottle

        rate = getattr(settings, "GLOBAL_RATE_LIMIT", None)

        if rate:
            throttle = SimpleRateThrottle()
            throttle.rate = rate
            throttle.scope = "global"

            if not throttle.allow_request(request, None):  # type: ignore
                wait = throttle.wait()
                return JsonResponse(
                    {
                        "error": {
                            "code": "rate_limit_exceeded",
                            "message": "Too many requests. Please try again later.",
                            "retry_after": wait,
                        }
                    },
                    status=429,
                )

        return self.get_response(request)
