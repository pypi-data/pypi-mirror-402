"""
Tests for SwiftAPI Exceptions.
"""
import pytest
from swiftapi.exceptions import (
    APIException,
    ValidationError,
    AuthenticationFailed,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    NotAcceptable,
    Throttled,
)


class TestExceptions:
    """Test exception classes."""
    
    def test_api_exception_basic(self):
        """Test basic APIException."""
        exc = APIException(detail="Something went wrong")
        assert exc.status_code == 500
        assert exc.detail == "Something went wrong"
    
    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError({"name": "This field is required"})
        assert exc.status_code == 400
        assert "name" in exc.detail
    
    def test_authentication_failed(self):
        """Test AuthenticationFailed."""
        exc = AuthenticationFailed()
        assert exc.status_code == 401
    
    def test_permission_denied(self):
        """Test PermissionDenied."""
        exc = PermissionDenied()
        assert exc.status_code == 403
    
    def test_not_found(self):
        """Test NotFound."""
        exc = NotFound()
        assert exc.status_code == 404
    
    def test_method_not_allowed(self):
        """Test MethodNotAllowed."""
        exc = MethodNotAllowed(method="POST")
        assert exc.status_code == 405
    
    def test_not_acceptable(self):
        """Test NotAcceptable."""
        exc = NotAcceptable()
        assert exc.status_code == 406
    
    def test_throttled(self):
        """Test Throttled."""
        exc = Throttled(wait=60)
        assert exc.status_code == 429
    
    def test_exception_detail_format(self):
        """Test exception detail format."""
        exc = ValidationError({"email": "Invalid email"})
        
        # ValidationError stores detail as dict
        assert isinstance(exc.detail, dict)
        assert "email" in exc.detail
        assert exc.status_code == 400


class TestExceptionMessages:
    """Test exception message formatting."""
    
    def test_custom_message(self):
        """Test custom exception message."""
        exc = NotFound(detail="User not found")
        assert exc.detail == "User not found"
    
    def test_default_message(self):
        """Test default exception message."""
        exc = NotFound()
        assert exc.detail is not None
        assert len(exc.detail) > 0
