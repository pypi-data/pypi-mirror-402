"""
Tests for SwiftAPI Throttling.
"""
import pytest
from swiftapi.throttling import (
    SimpleRateThrottle,
    AnonRateThrottle,
    UserRateThrottle,
    ScopedRateThrottle,
)


class TestSimpleRateThrottle:
    """Test SimpleRateThrottle."""
    
    def test_creation(self):
        """Test creating SimpleRateThrottle."""
        throttle = SimpleRateThrottle()
        assert throttle is not None
    
    def test_has_rate_attribute(self):
        """Test throttle has rate attribute."""
        throttle = SimpleRateThrottle()
        assert hasattr(throttle, 'rate') or hasattr(throttle.__class__, 'rate')


class TestAnonRateThrottle:
    """Test AnonRateThrottle."""
    
    def test_scope(self):
        """Test throttle scope."""
        throttle = AnonRateThrottle()
        assert throttle.scope == "anon"
    
    def test_creation(self):
        """Test creating AnonRateThrottle."""
        throttle = AnonRateThrottle()
        assert throttle is not None


class TestUserRateThrottle:
    """Test UserRateThrottle."""
    
    def test_scope(self):
        """Test throttle scope."""
        throttle = UserRateThrottle()
        assert throttle.scope == "user"
    
    def test_creation(self):
        """Test creating UserRateThrottle."""
        throttle = UserRateThrottle()
        assert throttle is not None


class TestScopedRateThrottle:
    """Test ScopedRateThrottle."""
    
    def test_creation(self):
        """Test creating ScopedRateThrottle."""
        throttle = ScopedRateThrottle()
        assert throttle is not None
    
    def test_custom_scope(self):
        """Test custom throttle scope."""
        throttle = ScopedRateThrottle()
        throttle.scope = "premium"
        assert throttle.scope == "premium"
