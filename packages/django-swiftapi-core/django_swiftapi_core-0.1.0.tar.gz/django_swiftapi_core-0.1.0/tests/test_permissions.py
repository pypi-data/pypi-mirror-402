"""
Tests for SwiftAPI Permissions.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from swiftapi.permissions import (
    AllowAny,
    DenyAll,
    IsAuthenticated,
    IsAdminUser,
    and_permissions,
    or_permissions,
)


class TestBasicPermissions:
    """Test basic permission classes."""
    
    @pytest.mark.asyncio
    async def test_allow_any(self):
        """Test AllowAny permission."""
        permission = AllowAny()
        request = Mock()
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_deny_all(self):
        """Test DenyAll permission."""
        permission = DenyAll()
        request = Mock()
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_authenticated_with_user(self):
        """Test IsAuthenticated with authenticated user."""
        permission = IsAuthenticated()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_authenticated_without_user(self):
        """Test IsAuthenticated with anonymous user."""
        permission = IsAuthenticated()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_admin_user(self):
        """Test IsAdminUser permission."""
        permission = IsAdminUser()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_staff = True
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_admin_user_non_admin(self):
        """Test IsAdminUser with non-admin user."""
        permission = IsAdminUser()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_staff = False
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is False


class TestPermissionCombinators:
    """Test permission combinators."""
    
    @pytest.mark.asyncio
    async def test_and_permissions_all_pass(self):
        """Test and_permissions when all permissions pass."""
        combined = and_permissions(AllowAny, AllowAny)
        permission = combined()
        request = Mock()
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_and_permissions_one_fails(self):
        """Test and_permissions when one permission fails."""
        combined = and_permissions(AllowAny, DenyAll)
        permission = combined()
        request = Mock()
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_or_permissions_one_passes(self):
        """Test or_permissions when one permission passes."""
        combined = or_permissions(AllowAny, DenyAll)
        permission = combined()
        request = Mock()
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_or_permissions_all_fail(self):
        """Test or_permissions when all permissions fail."""
        combined = or_permissions(DenyAll, DenyAll)
        permission = combined()
        request = Mock()
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is False
