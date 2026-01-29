"""
Django Integration Tests for SwiftAPI.

These tests verify that SwiftAPI works correctly with Django's
ORM, request/response cycle, and middleware.
"""
import pytest
from django.test import RequestFactory, AsyncRequestFactory
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from swiftapi.viewsets import ViewSet, ModelViewSet
from swiftapi.responses import SuccessResponse, ErrorResponse
from swiftapi.exceptions import NotFound, ValidationError
from swiftapi.permissions import AllowAny, IsAuthenticated


User = get_user_model()


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def async_request_factory():
    """Django async request factory."""
    return AsyncRequestFactory()


class TestRequestHandling:
    """Test Django request handling."""
    
    def test_get_request(self, request_factory):
        """Test handling GET request."""
        request = request_factory.get('/api/test/')
        assert request.method == 'GET'
    
    def test_post_request_with_json(self, request_factory):
        """Test handling POST request with JSON body."""
        request = request_factory.post(
            '/api/test/',
            data='{"name": "John"}',
            content_type='application/json'
        )
        assert request.method == 'POST'
        assert request.content_type == 'application/json'
    
    def test_put_request(self, request_factory):
        """Test handling PUT request."""
        request = request_factory.put(
            '/api/test/1/',
            data='{"name": "Updated"}',
            content_type='application/json'
        )
        assert request.method == 'PUT'
    
    def test_delete_request(self, request_factory):
        """Test handling DELETE request."""
        request = request_factory.delete('/api/test/1/')
        assert request.method == 'DELETE'
    
    def test_request_with_headers(self, request_factory):
        """Test request with custom headers."""
        request = request_factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION='Bearer token123',
            HTTP_ACCEPT='application/json'
        )
        assert 'HTTP_AUTHORIZATION' in request.META
        assert request.META['HTTP_AUTHORIZATION'] == 'Bearer token123'


class TestResponseGeneration:
    """Test response generation."""
    
    def test_success_response_status(self):
        """Test SuccessResponse has correct status."""
        response = SuccessResponse(data={'id': 1})
        assert response.status_code == 200
    
    def test_success_response_content_type(self):
        """Test SuccessResponse content type."""
        response = SuccessResponse(data={})
        assert 'application/json' in response['Content-Type']
    
    def test_error_response_status(self):
        """Test ErrorResponse with custom status."""
        response = ErrorResponse(
            message='Not found',
            code='not_found',
            status=404
        )
        assert response.status_code == 404


class TestViewSetIntegration:
    """Test ViewSet with Django."""
    
    def test_viewset_creation(self):
        """Test creating a ViewSet."""
        class TestViewSet(ViewSet):
            permission_classes = [AllowAny]
            
            async def list(self, request):
                return [{'id': 1}, {'id': 2}]
        
        viewset = TestViewSet()
        assert viewset is not None
        assert viewset.permission_classes == [AllowAny]
    
    def test_viewset_with_permissions(self):
        """Test ViewSet with permission classes."""
        class SecureViewSet(ViewSet):
            permission_classes = [IsAuthenticated]
        
        viewset = SecureViewSet()
        assert IsAuthenticated in viewset.permission_classes


class TestExceptionHandling:
    """Test exception handling in Django context."""
    
    def test_not_found_exception(self):
        """Test NotFound exception."""
        exc = NotFound(detail='Resource not found')
        assert exc.status_code == 404
        assert 'not found' in exc.detail.lower()
    
    def test_validation_error_with_fields(self):
        """Test ValidationError with field errors."""
        exc = ValidationError({
            'email': 'Invalid email format',
            'password': 'Password too short'
        })
        assert exc.status_code == 400
        assert 'email' in exc.detail
        assert 'password' in exc.detail


@pytest.mark.django_db
class TestDatabaseIntegration:
    """Test database integration."""
    
    def test_user_model_available(self):
        """Test User model is available."""
        assert User is not None
    
    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.pk is not None
        assert user.username == 'testuser'
    
    def test_authenticate_user(self):
        """Test user authentication."""
        from django.contrib.auth import authenticate
        
        User.objects.create_user(
            username='authtest',
            email='auth@example.com',
            password='authpass123'
        )
        
        user = authenticate(username='authtest', password='authpass123')
        assert user is not None
        assert user.username == 'authtest'
    
    def test_user_is_authenticated(self):
        """Test user is_authenticated property."""
        user = User.objects.create_user(
            username='activeuser',
            email='active@example.com',
            password='activepass123'
        )
        assert user.is_authenticated is True


@pytest.mark.asyncio
class TestAsyncIntegration:
    """Test async functionality."""
    
    async def test_async_viewset_method(self):
        """Test async ViewSet method."""
        class AsyncViewSet(ViewSet):
            async def list(self, request):
                return [{'id': 1}]
        
        viewset = AsyncViewSet()
        # The method should be a coroutine function
        import inspect
        assert inspect.iscoroutinefunction(viewset.list)
    
    async def test_async_permission_check(self):
        """Test async permission checking."""
        from unittest.mock import Mock
        
        permission = AllowAny()
        request = Mock()
        view = Mock()
        
        result = await permission.has_permission(request, view)
        assert result is True
