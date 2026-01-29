"""
Tests for SwiftAPI Versioning.
"""
import pytest
from swiftapi.versioning import (
    URLPathVersioning,
    QueryParameterVersioning,
    HeaderVersioning,
    NamespaceVersioning,
    VersionedRouter,
)


class TestURLPathVersioning:
    """Test URLPathVersioning."""
    
    def test_creation(self):
        """Test creating URLPathVersioning."""
        versioning = URLPathVersioning()
        assert versioning is not None
    
    def test_default_version(self):
        """Test default version."""
        versioning = URLPathVersioning(default_version="v1")
        assert versioning.default_version == "v1"


class TestQueryParameterVersioning:
    """Test QueryParameterVersioning."""
    
    def test_creation(self):
        """Test creating QueryParameterVersioning."""
        versioning = QueryParameterVersioning()
        assert versioning is not None
    
    def test_version_param(self):
        """Test version parameter name."""
        versioning = QueryParameterVersioning()
        assert versioning.version_param == "version"


class TestHeaderVersioning:
    """Test HeaderVersioning."""
    
    def test_creation(self):
        """Test creating HeaderVersioning."""
        versioning = HeaderVersioning()
        assert versioning is not None
    
    def test_has_header_name(self):
        """Test has header name attribute."""
        versioning = HeaderVersioning()
        assert hasattr(versioning, 'header_name')


class TestNamespaceVersioning:
    """Test NamespaceVersioning."""
    
    def test_creation(self):
        """Test creating NamespaceVersioning."""
        versioning = NamespaceVersioning()
        assert versioning is not None


class TestVersionedRouter:
    """Test VersionedRouter."""
    
    def test_creation(self):
        """Test creating VersionedRouter."""
        router = VersionedRouter()
        assert router is not None
