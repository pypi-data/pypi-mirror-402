"""
Tests for SwiftAPI Decorators.
"""
import pytest
from swiftapi.decorators import (
    api_view,
    action,
    permission_classes,
    authentication_classes,
    throttle_classes,
)


class TestDecorators:
    """Test decorator functions."""
    
    def test_api_view_decorator(self):
        """Test @api_view decorator attributes."""
        @api_view(["GET", "POST"])
        async def my_view(request):
            pass
        
        assert hasattr(my_view, "methods")
        assert "GET" in my_view.methods
        assert "POST" in my_view.methods
    
    def test_action_decorator(self):
        """Test @action decorator."""
        @action(detail=True, methods=["POST"])
        def custom_action(self, request, pk):
            pass
        
        assert custom_action._is_action is True
        assert custom_action.detail is True
        assert "POST" in custom_action.methods
    
    def test_action_decorator_defaults(self):
        """Test @action decorator with defaults."""
        @action()
        def list_action(self, request):
            pass
        
        assert list_action.detail is True
        assert "GET" in list_action.methods
    
    def test_permission_classes_decorator(self):
        """Test @permission_classes decorator."""
        from swiftapi.permissions import IsAuthenticated
        
        @permission_classes([IsAuthenticated])
        def protected_view(request):
            pass
        
        assert hasattr(protected_view, "permission_classes")
        assert IsAuthenticated in protected_view.permission_classes


class TestActionURLPath:
    """Test action URL path generation."""
    
    def test_action_url_path_default(self):
        """Test default URL path from function name."""
        @action(detail=True)
        def reset_password(self, request, pk):
            pass
        
        assert reset_password.url_path == "reset_password"
    
    def test_action_url_path_custom(self):
        """Test custom URL path."""
        @action(detail=True, url_path="reset-password")
        def reset_password(self, request, pk):
            pass
        
        assert reset_password.url_path == "reset-password"
    
    def test_action_url_name(self):
        """Test action URL name generation."""
        @action(detail=False, url_name="user-me")
        def me(self, request):
            pass
        
        assert me.url_name == "user-me"
