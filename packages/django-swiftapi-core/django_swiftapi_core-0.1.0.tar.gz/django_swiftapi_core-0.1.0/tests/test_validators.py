"""
Tests for SwiftAPI Validators.
"""
import pytest
from swiftapi.validators import (
    min_length,
    max_length,
    min_value,
    max_value,
    regex_validator,
    email_validator,
    url_validator,
    slug_validator,
)
from swiftapi.exceptions import ValidationError


class TestStringValidators:
    """Test string validators."""
    
    def test_min_length_valid(self):
        """Test min_length with valid string."""
        validator = min_length(3)
        validator("hello")  # Should not raise
    
    def test_min_length_invalid(self):
        """Test min_length with too short string."""
        validator = min_length(5)
        with pytest.raises(ValidationError):
            validator("hi")
    
    def test_max_length_valid(self):
        """Test max_length with valid string."""
        validator = max_length(10)
        validator("hello")  # Should not raise
    
    def test_max_length_invalid(self):
        """Test max_length with too long string."""
        validator = max_length(3)
        with pytest.raises(ValidationError):
            validator("hello world")
    
    def test_regex_validator_valid(self):
        """Test regex_validator with matching pattern."""
        validator = regex_validator(r"^\d{3}-\d{4}$")
        validator("123-4567")  # Should not raise
    
    def test_regex_validator_invalid(self):
        """Test regex_validator with non-matching pattern."""
        validator = regex_validator(r"^\d{3}-\d{4}$")
        with pytest.raises(ValidationError):
            validator("invalid")
    
    def test_email_validator_valid(self):
        """Test email_validator with valid email."""
        validator = email_validator()
        validator("test@example.com")  # Should not raise
    
    def test_email_validator_invalid(self):
        """Test email_validator with invalid email."""
        validator = email_validator()
        with pytest.raises(ValidationError):
            validator("not-an-email")
    
    def test_url_validator_valid(self):
        """Test url_validator with valid URL."""
        validator = url_validator()
        validator("https://example.com")  # Should not raise
    
    def test_slug_validator_valid(self):
        """Test slug_validator with valid slug."""
        validator = slug_validator()
        validator("my-slug-123")  # Should not raise
    
    def test_slug_validator_invalid(self):
        """Test slug_validator with invalid slug."""
        validator = slug_validator()
        with pytest.raises(ValidationError):
            validator("invalid slug!")


class TestNumericValidators:
    """Test numeric validators."""
    
    def test_min_value_valid(self):
        """Test min_value with valid number."""
        validator = min_value(0)
        validator(10)  # Should not raise
    
    def test_min_value_invalid(self):
        """Test min_value with too small number."""
        validator = min_value(10)
        with pytest.raises(ValidationError):
            validator(5)
    
    def test_max_value_valid(self):
        """Test max_value with valid number."""
        validator = max_value(100)
        validator(50)  # Should not raise
    
    def test_max_value_invalid(self):
        """Test max_value with too large number."""
        validator = max_value(10)
        with pytest.raises(ValidationError):
            validator(100)
