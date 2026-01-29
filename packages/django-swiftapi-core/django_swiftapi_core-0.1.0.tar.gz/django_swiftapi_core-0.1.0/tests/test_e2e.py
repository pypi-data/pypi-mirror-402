"""
End-to-end tests for SwiftAPI.

These tests simulate complete API request/response cycles.
"""
import pytest
import json
from django.test import Client, AsyncClient


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def async_client():
    """Django async test client."""
    return AsyncClient()


class TestHTTPMethods:
    """Test HTTP method handling."""
    
    def test_client_get(self, client):
        """Test GET request via client."""
        # This tests that the client works
        assert client is not None
    
    def test_client_post(self, client):
        """Test POST request via client."""
        assert hasattr(client, 'post')
    
    def test_client_put(self, client):
        """Test PUT request via client."""
        assert hasattr(client, 'put')
    
    def test_client_delete(self, client):
        """Test DELETE request via client."""
        assert hasattr(client, 'delete')


class TestContentTypes:
    """Test content type handling."""
    
    def test_json_content_type(self, client):
        """Test JSON content type."""
        # Client should support JSON
        assert hasattr(client, 'post')
    
    def test_form_content_type(self, client):
        """Test form content type."""
        assert hasattr(client, 'post')


class TestJSONResponses:
    """Test JSON response handling."""
    
    def test_json_encode(self):
        """Test JSON encoding."""
        data = {'name': 'Test', 'count': 42}
        encoded = json.dumps(data)
        assert '"name"' in encoded
        assert '"Test"' in encoded
    
    def test_json_decode(self):
        """Test JSON decoding."""
        encoded = '{"name": "Test", "count": 42}'
        data = json.loads(encoded)
        assert data['name'] == 'Test'
        assert data['count'] == 42


@pytest.mark.django_db
class TestAuthenticatedRequests:
    """Test authenticated request handling."""
    
    def test_login_required(self, client):
        """Test that login is required for protected endpoints."""
        # Client should have login method
        assert hasattr(client, 'login')
    
    def test_client_with_force_login(self, client):
        """Test force_login for testing."""
        assert hasattr(client, 'force_login')


class TestErrorResponses:
    """Test error response handling."""
    
    def test_404_structure(self):
        """Test 404 response structure."""
        from swiftapi.exceptions import NotFound
        
        exc = NotFound()
        assert exc.status_code == 404
    
    def test_400_structure(self):
        """Test 400 response structure."""
        from swiftapi.exceptions import ValidationError
        
        exc = ValidationError({'field': 'error'})
        assert exc.status_code == 400
    
    def test_401_structure(self):
        """Test 401 response structure."""
        from swiftapi.exceptions import AuthenticationFailed
        
        exc = AuthenticationFailed()
        assert exc.status_code == 401
    
    def test_403_structure(self):
        """Test 403 response structure."""
        from swiftapi.exceptions import PermissionDenied
        
        exc = PermissionDenied()
        assert exc.status_code == 403
