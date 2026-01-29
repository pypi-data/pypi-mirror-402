"""
Tests for SwiftAPI Routing.
"""
import pytest
from swiftapi.routing import Router, SimpleRouter, NestedRouter


class MockViewSet:
    """Mock ViewSet for testing."""
    model = None
    
    @classmethod
    def as_view(cls, actions):
        def view(request, *args, **kwargs):
            return {"actions": actions}
        return view
    
    async def list(self, request):
        return []
    
    async def retrieve(self, request, pk):
        return {"id": pk}
    
    async def create(self, request):
        return {"created": True}


class TestRouter:
    """Test Router class."""
    
    def test_router_register(self):
        """Test registering a viewset."""
        router = Router()
        router.register("users", MockViewSet)
        
        assert len(router._registry) == 1
        assert router._registry[0][0] == "users"
    
    def test_router_get_urls(self):
        """Test generating URL patterns."""
        router = Router()
        router.register("users", MockViewSet)
        
        urls = router.get_urls()
        assert len(urls) > 0
    
    def test_router_multiple_viewsets(self):
        """Test registering multiple viewsets."""
        router = Router()
        router.register("users", MockViewSet)
        router.register("posts", MockViewSet)
        
        assert len(router._registry) == 2


class TestSimpleRouter:
    """Test SimpleRouter class."""
    
    def test_simple_router(self):
        """Test SimpleRouter basic functionality."""
        router = SimpleRouter()
        router.register("items", MockViewSet)
        
        urls = router.get_urls()
        assert len(urls) > 0


class TestNestedRouter:
    """Test NestedRouter class."""
    
    def test_nested_router(self):
        """Test NestedRouter for nested resources."""
        parent_router = Router()
        parent_router.register("users", MockViewSet)
        
        nested_router = NestedRouter(parent_router, "users", lookup="user")
        nested_router.register("posts", MockViewSet)
        
        # Should create nested URLs like /users/{user_pk}/posts/
        urls = nested_router.get_urls()
        assert len(urls) > 0
