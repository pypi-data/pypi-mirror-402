"""
SwiftAPI Testing Utilities.

Test client and helpers for testing async API endpoints.
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any
from unittest import TestCase

from django.test import Client, RequestFactory

if TYPE_CHECKING:
    from django.http import JsonResponse


class AsyncAPIClient:
    """
    Async-compatible API test client.

    Similar to DRF's APIClient but designed for async viewsets.

    Usage:
        from swiftapi.testing import AsyncAPIClient

        class TestUserAPI(TestCase):
            async def test_list_users(self):
                client = AsyncAPIClient()
                response = await client.get("/api/users/")
                self.assertEqual(response.status_code, 200)
    """

    def __init__(self) -> None:
        self.client = Client()
        self.factory = RequestFactory()
        self._auth_header: dict[str, str] = {}
        self._default_headers: dict[str, str] = {}

    def set_token(self, token: str) -> None:
        """
        Set authentication token for requests.

        Args:
            token: Token value (without "Token" prefix)
        """
        self._auth_header = {"HTTP_AUTHORIZATION": f"Token {token}"}

    def set_jwt(self, token: str) -> None:
        """
        Set JWT token for requests.

        Args:
            token: JWT token value
        """
        self._auth_header = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def clear_auth(self) -> None:
        """Clear authentication."""
        self._auth_header = {}

    def set_header(self, name: str, value: str) -> None:
        """
        Set a default header for all requests.

        Args:
            name: Header name (e.g., "X-Tenant-ID")
            value: Header value
        """
        # Convert to Django META format
        meta_name = f"HTTP_{name.upper().replace('-', '_')}"
        self._default_headers[meta_name] = value

    async def get(
        self,
        path: str,
        data: dict | None = None,
        **extra: Any,
    ) -> JsonResponse:
        """
        Make a GET request.

        Args:
            path: URL path
            data: Query parameters
            **extra: Additional request options
        """
        return await self._request("GET", path, data=data, **extra)

    async def post(
        self,
        path: str,
        data: Any = None,
        content_type: str = "application/json",
        **extra: Any,
    ) -> JsonResponse:
        """
        Make a POST request.

        Args:
            path: URL path
            data: Request body data
            content_type: Content type
            **extra: Additional request options
        """
        return await self._request(
            "POST", path, data=data, content_type=content_type, **extra
        )

    async def put(
        self,
        path: str,
        data: Any = None,
        content_type: str = "application/json",
        **extra: Any,
    ) -> JsonResponse:
        """
        Make a PUT request.

        Args:
            path: URL path
            data: Request body data
            content_type: Content type
            **extra: Additional request options
        """
        return await self._request(
            "PUT", path, data=data, content_type=content_type, **extra
        )

    async def patch(
        self,
        path: str,
        data: Any = None,
        content_type: str = "application/json",
        **extra: Any,
    ) -> JsonResponse:
        """
        Make a PATCH request.

        Args:
            path: URL path
            data: Request body data
            content_type: Content type
            **extra: Additional request options
        """
        return await self._request(
            "PATCH", path, data=data, content_type=content_type, **extra
        )

    async def delete(
        self,
        path: str,
        data: Any = None,
        **extra: Any,
    ) -> JsonResponse:
        """
        Make a DELETE request.

        Args:
            path: URL path
            data: Request body data
            **extra: Additional request options
        """
        return await self._request("DELETE", path, data=data, **extra)

    async def _request(
        self,
        method: str,
        path: str,
        data: Any = None,
        content_type: str = "application/json",
        **extra: Any,
    ) -> JsonResponse:
        """Make an HTTP request."""
        # Merge headers
        headers = {**self._default_headers, **self._auth_header, **extra}

        # Prepare data
        if data is not None and content_type == "application/json":
            if isinstance(data, (dict, list)):
                data = json.dumps(data)

        # Run sync Django test client in executor
        loop = asyncio.get_event_loop()

        def make_request():
            client_method = getattr(self.client, method.lower())
            return client_method(
                path,
                data=data,
                content_type=content_type if method != "GET" else None,
                **headers,
            )

        response = await loop.run_in_executor(None, make_request)
        return response

    def json(self, response: Any) -> dict:
        """
        Parse JSON response body.

        Args:
            response: Response object

        Returns:
            Parsed JSON data
        """
        if hasattr(response, "json"):
            return response.json()
        return json.loads(response.content)


class AsyncTestCase(TestCase):
    """
    Base TestCase for async tests.

    Provides setup for async test environment.

    Usage:
        from swiftapi.testing import AsyncTestCase, AsyncAPIClient

        class TestUserAPI(AsyncTestCase):
            client_class = AsyncAPIClient

            async def test_list_users(self):
                response = await self.client.get("/api/users/")
                self.assertEqual(response.status_code, 200)
    """

    client_class = AsyncAPIClient

    def setUp(self) -> None:
        """Set up test client."""
        super().setUp()
        self.client = self.client_class()

    def _callTestMethod(self, method):
        """Run async test methods."""
        if asyncio.iscoroutinefunction(method):
            asyncio.run(method())
        else:
            method()


# Assertion helpers

def assert_status(response: Any, expected: int) -> None:
    """
    Assert response status code.

    Args:
        response: Response object
        expected: Expected status code

    Raises:
        AssertionError: If status doesn't match
    """
    actual = response.status_code
    assert actual == expected, f"Expected status {expected}, got {actual}"


def assert_contains(response: Any, text: str) -> None:
    """
    Assert response contains text.

    Args:
        response: Response object
        text: Text to find in response
    """
    content = response.content.decode("utf-8")
    assert text in content, f"'{text}' not found in response"


def assert_json_equal(response: Any, expected: dict) -> None:
    """
    Assert response JSON equals expected.

    Args:
        response: Response object
        expected: Expected JSON data
    """
    actual = json.loads(response.content)
    assert actual == expected, f"Expected {expected}, got {actual}"


def assert_data_contains(response: Any, key: str, value: Any) -> None:
    """
    Assert response data contains key-value pair.

    Args:
        response: Response object
        key: Key to check
        value: Expected value
    """
    data = json.loads(response.content)

    if "data" in data:
        data = data["data"]

    assert key in data, f"Key '{key}' not found in response"
    assert data[key] == value, f"Expected {key}={value}, got {key}={data[key]}"


# Factory helpers for creating test data

class SchemaFactory:
    """
    Factory for creating test data that matches schemas.

    Usage:
        from swiftapi.testing import SchemaFactory
        from myapp.schemas import UserSchema

        factory = SchemaFactory(UserSchema)
        user_data = factory.build()  # Random valid data
        user_data = factory.build(name="John")  # Override specific fields
    """

    def __init__(self, schema_class: type) -> None:
        """
        Initialize factory.

        Args:
            schema_class: Schema class to generate data for
        """
        self.schema_class = schema_class

    def build(self, **overrides: Any) -> dict[str, Any]:
        """
        Build a valid data dictionary.

        Args:
            **overrides: Field values to override

        Returns:
            Valid data dictionary
        """

        data: dict[str, Any] = {}
        fields = getattr(self.schema_class, "_fields", {})

        for field_name, (field_type, field_info) in fields.items():
            if field_name in overrides:
                data[field_name] = overrides[field_name]
                continue

            if field_info.read_only:
                continue

            if field_info.has_default():
                data[field_name] = field_info.get_default()
                continue

            # Generate random value based on type
            data[field_name] = self._generate_value(field_type)

        data.update(overrides)
        return data

    def _generate_value(self, field_type: type) -> Any:
        """Generate a random value for the given type."""
        import datetime
        import random
        import string
        import uuid

        if field_type is str:
            return "".join(random.choices(string.ascii_letters, k=10))

        if field_type is int:
            return random.randint(1, 1000)

        if field_type is float:
            return random.uniform(0.0, 100.0)

        if field_type is bool:
            return random.choice([True, False])

        if field_type is datetime.datetime:
            return datetime.datetime.now().isoformat()

        if field_type is datetime.date:
            return datetime.date.today().isoformat()

        if field_type is uuid.UUID:
            return str(uuid.uuid4())

        return None

    def build_many(self, count: int = 3, **overrides: Any) -> list[dict[str, Any]]:
        """
        Build multiple valid data dictionaries.

        Args:
            count: Number of items to generate
            **overrides: Field values to override for all items

        Returns:
            List of valid data dictionaries
        """
        return [self.build(**overrides) for _ in range(count)]
