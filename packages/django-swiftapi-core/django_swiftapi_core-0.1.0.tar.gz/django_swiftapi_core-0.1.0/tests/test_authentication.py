"""
Tests for SwiftAPI Authentication.
"""
import pytest
from swiftapi.authentication import (
    BasicAuthentication,
    TokenAuthentication,
    BearerTokenAuthentication,
    SessionAuthentication,
    JWTAuthentication,
    APIKeyAuthentication,
)


class TestBasicAuthentication:
    """Test BasicAuthentication."""
    
    def test_basic_auth_creation(self):
        """Test creating BasicAuthentication."""
        auth = BasicAuthentication()
        assert auth is not None


class TestTokenAuthentication:
    """Test TokenAuthentication."""
    
    def test_token_auth_creation(self):
        """Test creating TokenAuthentication."""
        auth = TokenAuthentication()
        assert auth is not None
    
    def test_keyword(self):
        """Test authentication keyword."""
        auth = TokenAuthentication()
        assert auth.keyword == "Token"


class TestBearerTokenAuthentication:
    """Test BearerTokenAuthentication."""
    
    def test_bearer_auth_creation(self):
        """Test creating BearerTokenAuthentication."""
        auth = BearerTokenAuthentication()
        assert auth is not None
    
    def test_bearer_keyword(self):
        """Test Bearer keyword."""
        auth = BearerTokenAuthentication()
        assert auth.keyword == "Bearer"


class TestSessionAuthentication:
    """Test SessionAuthentication."""
    
    def test_session_auth_creation(self):
        """Test creating SessionAuthentication."""
        auth = SessionAuthentication()
        assert auth is not None


class TestJWTAuthentication:
    """Test JWTAuthentication."""
    
    def test_jwt_auth_creation(self):
        """Test creating JWTAuthentication."""
        auth = JWTAuthentication()
        assert auth is not None
    
    def test_jwt_keyword(self):
        """Test JWT uses Bearer keyword."""
        auth = JWTAuthentication()
        assert auth.keyword == "Bearer"


class TestAPIKeyAuthentication:
    """Test APIKeyAuthentication."""
    
    def test_api_key_auth_creation(self):
        """Test creating APIKeyAuthentication."""
        auth = APIKeyAuthentication()
        assert auth is not None
    
    def test_has_header_attribute(self):
        """Test API key has header attribute."""
        auth = APIKeyAuthentication()
        # May use different attribute names
        assert hasattr(auth, 'header_name') or hasattr(auth, 'header')
