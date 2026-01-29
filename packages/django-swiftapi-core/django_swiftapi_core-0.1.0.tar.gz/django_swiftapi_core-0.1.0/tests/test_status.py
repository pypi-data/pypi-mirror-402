"""
Tests for SwiftAPI Status Codes.
"""
from swiftapi.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    is_success,
    is_client_error,
    is_server_error,
    is_redirect,
    is_informational,
)


class TestStatusCodes:
    """Test status code constants."""
    
    def test_success_codes(self):
        """Test success status codes."""
        assert HTTP_200_OK == 200
        assert HTTP_201_CREATED == 201
        assert HTTP_204_NO_CONTENT == 204
    
    def test_client_error_codes(self):
        """Test client error status codes."""
        assert HTTP_400_BAD_REQUEST == 400
        assert HTTP_401_UNAUTHORIZED == 401
        assert HTTP_403_FORBIDDEN == 403
        assert HTTP_404_NOT_FOUND == 404
        assert HTTP_405_METHOD_NOT_ALLOWED == 405
        assert HTTP_429_TOO_MANY_REQUESTS == 429
    
    def test_server_error_codes(self):
        """Test server error status codes."""
        assert HTTP_500_INTERNAL_SERVER_ERROR == 500


class TestStatusHelpers:
    """Test status code helper functions."""
    
    def test_is_success(self):
        """Test is_success helper."""
        assert is_success(200) is True
        assert is_success(201) is True
        assert is_success(204) is True
        assert is_success(400) is False
        assert is_success(500) is False
    
    def test_is_client_error(self):
        """Test is_client_error helper."""
        assert is_client_error(400) is True
        assert is_client_error(404) is True
        assert is_client_error(499) is True
        assert is_client_error(200) is False
        assert is_client_error(500) is False
    
    def test_is_server_error(self):
        """Test is_server_error helper."""
        assert is_server_error(500) is True
        assert is_server_error(503) is True
        assert is_server_error(400) is False
        assert is_server_error(200) is False
    
    def test_is_redirect(self):
        """Test is_redirect helper."""
        assert is_redirect(301) is True
        assert is_redirect(302) is True
        assert is_redirect(200) is False
    
    def test_is_informational(self):
        """Test is_informational helper."""
        assert is_informational(100) is True
        assert is_informational(101) is True
        assert is_informational(200) is False
