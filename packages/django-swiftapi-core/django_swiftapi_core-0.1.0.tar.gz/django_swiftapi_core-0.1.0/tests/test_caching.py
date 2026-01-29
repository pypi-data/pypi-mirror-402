"""
Tests for SwiftAPI Caching.
"""
import pytest
from swiftapi.caching import (
    cache_response,
    CacheBackend,
    InMemoryCacheBackend,
)


class TestInMemoryCacheBackend:
    """Test InMemoryCacheBackend."""
    
    def test_set_and_get(self):
        """Test setting and getting cache values."""
        cache = InMemoryCacheBackend()
        cache.set("key1", "value1", ttl=300)
        
        result = cache.get("key1")
        assert result == "value1"
    
    def test_get_missing_key(self):
        """Test getting a missing key returns None."""
        cache = InMemoryCacheBackend()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_delete(self):
        """Test deleting cache values."""
        cache = InMemoryCacheBackend()
        cache.set("key2", "value2", ttl=300)
        cache.delete("key2")
        
        result = cache.get("key2")
        assert result is None


class TestCacheResponseDecorator:
    """Test @cache_response decorator."""
    
    def test_decorator_exists(self):
        """Test cache_response decorator exists."""
        assert callable(cache_response)
    
    def test_decorator_with_timeout(self):
        """Test decorator with timeout parameter."""
        @cache_response(ttl=300)
        async def my_view(request):
            return {"data": "value"}
        
        assert callable(my_view)
