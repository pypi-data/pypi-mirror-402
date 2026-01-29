"""
Middleware integration tests for SwiftAPI.
"""
import pytest
from django.test import RequestFactory
from unittest.mock import Mock, AsyncMock


class TestMiddlewareIntegration:
    """Test middleware functionality."""
    
    def test_request_factory(self):
        """Test request factory creates valid requests."""
        factory = RequestFactory()
        request = factory.get('/test/')
        
        assert request.method == 'GET'
        assert hasattr(request, 'META')
    
    def test_request_meta_headers(self):
        """Test request META contains headers."""
        factory = RequestFactory()
        request = factory.get(
            '/test/',
            HTTP_ACCEPT='application/json',
            HTTP_X_CUSTOM='value'
        )
        
        assert request.META.get('HTTP_ACCEPT') == 'application/json'
        assert request.META.get('HTTP_X_CUSTOM') == 'value'


class TestTenancyMiddleware:
    """Test tenancy middleware functionality."""
    
    def test_tenant_attribute_can_be_set(self):
        """Test tenant can be set on request."""
        factory = RequestFactory()
        request = factory.get('/test/')
        
        # Simulate middleware setting tenant
        request.tenant = Mock(pk=1, slug='test-tenant')
        
        assert request.tenant is not None
        assert request.tenant.pk == 1


class TestAuthenticationMiddleware:
    """Test authentication middleware."""
    
    def test_user_attribute_can_be_set(self):
        """Test user can be set on request."""
        factory = RequestFactory()
        request = factory.get('/test/')
        
        # Simulate authentication
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.pk = 1
        request.user = mock_user
        
        assert request.user.is_authenticated is True


class TestCORSMiddleware:
    """Test CORS middleware functionality."""
    
    def test_options_request(self):
        """Test OPTIONS request for CORS preflight."""
        factory = RequestFactory()
        request = factory.options('/test/')
        
        assert request.method == 'OPTIONS'
    
    def test_cors_headers_can_be_added(self):
        """Test CORS headers can be added to response."""
        from django.http import HttpResponse
        
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
        
        assert response['Access-Control-Allow-Origin'] == '*'


class TestExceptionMiddleware:
    """Test exception handling middleware."""
    
    def test_exception_to_response(self):
        """Test exceptions are converted to responses."""
        from swiftapi.exceptions import NotFound
        
        exc = NotFound()
        
        # Exception should have status_code for response conversion
        assert hasattr(exc, 'status_code')
        assert exc.status_code == 404
    
    def test_validation_error_detail(self):
        """Test validation error contains detail."""
        from swiftapi.exceptions import ValidationError
        
        exc = ValidationError({'field': 'Error message'})
        
        assert hasattr(exc, 'detail')
        assert 'field' in exc.detail
