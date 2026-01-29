"""
SwiftAPI Exception Classes.

Provides a hierarchy of exception classes with structured error responses
following consistent patterns for API error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.http import JsonResponse

if TYPE_CHECKING:
    from django.http import HttpRequest


class APIException(Exception):
    """
    Base exception for all SwiftAPI errors.

    All API exceptions should inherit from this class to ensure
    consistent error handling and response formatting.

    Attributes:
        status_code: HTTP status code for the error response
        default_code: Machine-readable error code
        default_detail: Human-readable error message
    """

    status_code: int = 500
    default_code: str = "error"
    default_detail: str = "A server error occurred."

    def __init__(
        self,
        detail: str | dict[str, Any] | list[Any] | None = None,
        code: str | None = None,
        field: str | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            detail: Error detail message or structured error data
            code: Machine-readable error code
            field: Field name if this is a field-specific error
        """
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        self.detail = detail
        self.code = code
        self.field = field
        super().__init__(detail)

    def get_error_response(self) -> dict[str, Any]:
        """
        Get the structured error response.

        Returns:
            Dict with error information in format:
            {"error": {"code": "...", "message": "...", "field": "..."}}
        """
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.detail if isinstance(self.detail, str) else str(self.detail),
        }

        if self.field:
            error["field"] = self.field

        # Handle structured detail (like validation errors)
        if isinstance(self.detail, (dict, list)):
            error["details"] = self.detail
            error["message"] = "Validation error" if self.code == "validation_error" else str(self.detail)

        return {"error": error}

    def __str__(self) -> str:
        return str(self.detail)


class ValidationError(APIException):
    """
    Exception for schema validation failures.

    Raised when input data fails validation against a schema.
    Returns 400 Bad Request with field-level error details.
    """

    status_code = 400
    default_code = "validation_error"
    default_detail = "Invalid input data."

    def __init__(
        self,
        detail: str | dict[str, Any] | list[Any] | None = None,
        code: str | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(detail, code or self.default_code, field)

    def get_error_response(self) -> dict[str, Any]:
        """Get structured validation error response."""
        if isinstance(self.detail, dict):
            # Field-level errors
            errors: list[dict[str, Any]] = []
            for field_name, messages in self.detail.items():
                if isinstance(messages, list):
                    for msg in messages:
                        errors.append({
                            "code": self.code,
                            "field": field_name,
                            "message": str(msg),
                        })
                else:
                    errors.append({
                        "code": self.code,
                        "field": field_name,
                        "message": str(messages),
                    })
            return {"errors": errors}
        elif isinstance(self.detail, list):
            errors = [
                {"code": self.code, "message": str(err)} for err in self.detail
            ]
            return {"errors": errors}
        else:
            return {"error": {
                "code": self.code,
                "message": str(self.detail),
                "field": self.field,
            }}


class ParseError(APIException):
    """
    Exception for malformed request data.

    Raised when the request body cannot be parsed (e.g., invalid JSON).
    Returns 400 Bad Request.
    """

    status_code = 400
    default_code = "parse_error"
    default_detail = "Malformed request data."


class AuthenticationFailed(APIException):
    """
    Exception for authentication failures.

    Raised when authentication credentials are invalid or expired.
    Returns 401 Unauthorized.
    """

    status_code = 401
    default_code = "authentication_failed"
    default_detail = "Invalid or expired authentication credentials."


class NotAuthenticated(APIException):
    """
    Exception for missing authentication.

    Raised when authentication is required but no credentials provided.
    Returns 401 Unauthorized.
    """

    status_code = 401
    default_code = "not_authenticated"
    default_detail = "Authentication credentials were not provided."


class PermissionDenied(APIException):
    """
    Exception for authorization failures.

    Raised when the authenticated user doesn't have required permissions.
    Returns 403 Forbidden.
    """

    status_code = 403
    default_code = "permission_denied"
    default_detail = "You do not have permission to perform this action."


class NotFound(APIException):
    """
    Exception for missing resources.

    Raised when a requested resource doesn't exist.
    Returns 404 Not Found.
    """

    status_code = 404
    default_code = "not_found"
    default_detail = "Resource not found."


class MethodNotAllowed(APIException):
    """
    Exception for unsupported HTTP methods.

    Raised when an HTTP method is not allowed on an endpoint.
    Returns 405 Method Not Allowed.
    """

    status_code = 405
    default_code = "method_not_allowed"
    default_detail = "Method not allowed."

    def __init__(
        self,
        method: str | None = None,
        detail: str | None = None,
        code: str | None = None,
    ) -> None:
        if detail is None and method:
            detail = f"Method '{method}' not allowed."
        super().__init__(detail, code)


class NotAcceptable(APIException):
    """
    Exception for unsupported content types.

    Raised when the client requests an unsupported response format.
    Returns 406 Not Acceptable.
    """

    status_code = 406
    default_code = "not_acceptable"
    default_detail = "Could not satisfy the request Accept header."


class Conflict(APIException):
    """
    Exception for conflict errors.

    Raised when a request conflicts with the current state of a resource.
    Returns 409 Conflict.
    """

    status_code = 409
    default_code = "conflict"
    default_detail = "Request conflicts with current state."


class UnsupportedMediaType(APIException):
    """
    Exception for unsupported request content types.

    Raised when the request body has an unsupported media type.
    Returns 415 Unsupported Media Type.
    """

    status_code = 415
    default_code = "unsupported_media_type"
    default_detail = "Unsupported media type in request."


class Throttled(APIException):
    """
    Exception for rate limit exceeded.

    Raised when a client exceeds their rate limit.
    Returns 429 Too Many Requests.
    """

    status_code = 429
    default_code = "throttled"
    default_detail = "Request was throttled."

    def __init__(
        self,
        wait: float | None = None,
        detail: str | None = None,
        code: str | None = None,
    ) -> None:
        """
        Initialize throttled exception.

        Args:
            wait: Seconds until throttle expires (for Retry-After header)
            detail: Error detail message
            code: Error code
        """
        self.wait = wait
        if detail is None and wait is not None:
            detail = f"Request was throttled. Try again in {int(wait)} seconds."
        super().__init__(detail, code)

    def get_error_response(self) -> dict[str, Any]:
        """Get error response with retry information."""
        response = super().get_error_response()
        if self.wait is not None:
            response["error"]["retry_after"] = int(self.wait)
        return response


class ServiceUnavailable(APIException):
    """
    Exception for service unavailable.

    Raised when the service is temporarily unavailable.
    Returns 503 Service Unavailable.
    """

    status_code = 503
    default_code = "service_unavailable"
    default_detail = "Service temporarily unavailable."


def default_exception_handler(
    exc: Exception,
    request: HttpRequest | None = None,
) -> JsonResponse:
    """
    Default exception handler for SwiftAPI.

    Converts exceptions to JSON responses with appropriate status codes.

    Args:
        exc: The exception to handle
        request: The current request (optional)

    Returns:
        JsonResponse with error details
    """
    if isinstance(exc, APIException):
        response = JsonResponse(
            exc.get_error_response(),
            status=exc.status_code,
        )

        # Add Retry-After header for throttled responses
        if isinstance(exc, Throttled) and exc.wait is not None:
            response["Retry-After"] = str(int(exc.wait))

        return response

    # Handle Django's Http404
    from django.http import Http404
    if isinstance(exc, Http404):
        not_found = NotFound()
        return JsonResponse(
            not_found.get_error_response(),
            status=not_found.status_code,
        )

    # Handle Django's PermissionDenied
    from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
    if isinstance(exc, DjangoPermissionDenied):
        denied = PermissionDenied()
        return JsonResponse(
            denied.get_error_response(),
            status=denied.status_code,
        )

    # Unhandled exceptions - return generic 500 error
    # In production, don't expose internal error details
    from django.conf import settings
    if settings.DEBUG:
        error_response = {
            "error": {
                "code": "internal_error",
                "message": str(exc),
                "type": type(exc).__name__,
            }
        }
    else:
        error_response = {
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
            }
        }

    return JsonResponse(error_response, status=500)


def api_exception_handler(
    exc: Exception,
    request: HttpRequest | None = None,
) -> JsonResponse | None:
    """
    API exception handler that can be used as Django middleware.

    Returns None for non-API exceptions to allow other handlers to process them.

    Args:
        exc: The exception to handle
        request: The current request

    Returns:
        JsonResponse for API exceptions, None otherwise
    """
    if isinstance(exc, APIException):
        return default_exception_handler(exc, request)
    return None
