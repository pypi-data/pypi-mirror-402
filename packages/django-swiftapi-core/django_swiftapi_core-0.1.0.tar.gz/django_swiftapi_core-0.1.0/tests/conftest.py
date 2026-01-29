"""
Test fixtures for SwiftAPI tests.
"""

import pytest


@pytest.fixture
def api_client():
    """Create an async API client."""
    from swiftapi.testing import AsyncAPIClient
    return AsyncAPIClient()
