"""
Tests for SwiftAPI OpenAPI/Swagger.
"""
import pytest
from swiftapi.openapi import (
    OpenAPIGenerator,
    get_openapi_view,
    get_swagger_ui_view,
)


class TestOpenAPIGenerator:
    """Test OpenAPIGenerator."""
    
    def test_creation(self):
        """Test creating OpenAPIGenerator."""
        generator = OpenAPIGenerator(title="My API", version="1.0.0")
        assert generator.title == "My API"
        assert generator.version == "1.0.0"
    
    def test_default_description(self):
        """Test default description."""
        generator = OpenAPIGenerator(title="API", version="1.0")
        # Description may be empty string or None
        assert generator.description is None or generator.description == ""
    
    def test_with_description(self):
        """Test with description."""
        generator = OpenAPIGenerator(
            title="API",
            version="1.0",
            description="My awesome API"
        )
        assert generator.description == "My awesome API"


class TestOpenAPIViews:
    """Test OpenAPI view generators."""
    
    def test_get_openapi_view_exists(self):
        """Test get_openapi_view function exists."""
        assert callable(get_openapi_view)
    
    def test_get_swagger_ui_view_exists(self):
        """Test get_swagger_ui_view function exists."""
        assert callable(get_swagger_ui_view)
