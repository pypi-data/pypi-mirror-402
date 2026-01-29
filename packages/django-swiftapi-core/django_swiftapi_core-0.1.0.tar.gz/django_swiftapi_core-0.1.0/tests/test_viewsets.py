"""
Tests for SwiftAPI ViewSets.
"""
import pytest
from swiftapi.viewsets import (
    ViewSet,
    GenericViewSet,
    ModelViewSet,
    ReadOnlyViewSet,
)


class TestViewSet:
    """Test ViewSet class."""
    
    def test_viewset_creation(self):
        """Test creating a ViewSet."""
        class MyViewSet(ViewSet):
            pass
        
        viewset = MyViewSet()
        assert viewset is not None
    
    def test_viewset_action_attribute(self):
        """Test ViewSet action attribute."""
        class MyViewSet(ViewSet):
            async def list(self, request):
                return []
        
        viewset = MyViewSet()
        viewset.action = "list"
        assert viewset.action == "list"


class TestGenericViewSet:
    """Test GenericViewSet class."""
    
    def test_creation(self):
        """Test creating GenericViewSet."""
        class MyViewSet(GenericViewSet):
            pass
        
        viewset = MyViewSet()
        assert viewset is not None


class TestModelViewSet:
    """Test ModelViewSet class."""
    
    def test_has_crud_methods(self):
        """Test ModelViewSet has CRUD methods."""
        viewset = ModelViewSet()
        
        assert hasattr(viewset, "list") or hasattr(viewset.__class__, "list")
        assert hasattr(viewset, "create") or hasattr(viewset.__class__, "create")
        assert hasattr(viewset, "retrieve") or hasattr(viewset.__class__, "retrieve")
        assert hasattr(viewset, "update") or hasattr(viewset.__class__, "update")
        assert hasattr(viewset, "destroy") or hasattr(viewset.__class__, "destroy")


class TestReadOnlyViewSet:
    """Test ReadOnlyViewSet class."""
    
    def test_has_read_methods(self):
        """Test ReadOnlyViewSet has read methods."""
        viewset = ReadOnlyViewSet()
        
        assert hasattr(viewset, "list") or hasattr(viewset.__class__, "list")
        assert hasattr(viewset, "retrieve") or hasattr(viewset.__class__, "retrieve")
