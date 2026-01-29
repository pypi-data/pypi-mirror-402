"""
Tests for SwiftAPI Filters.
"""
import pytest
from swiftapi.filters import (
    FilterSet,
    QueryFilter,
    SearchFilter,
    OrderingFilter,
)


class TestFilterSet:
    """Test FilterSet class."""
    
    def test_filterset_creation(self):
        """Test creating a FilterSet."""
        class UserFilterSet(FilterSet):
            class Meta:
                fields = ["name", "email", "is_active"]
        
        filterset = UserFilterSet()
        assert filterset is not None


class TestQueryFilter:
    """Test QueryFilter class."""
    
    def test_query_filter_creation(self):
        """Test creating a QueryFilter."""
        filter_obj = QueryFilter()
        assert filter_obj is not None
    
    def test_filter_fields(self):
        """Test filter fields configuration."""
        class MyFilter(QueryFilter):
            filter_fields = ["name", "status"]
        
        filter_obj = MyFilter()
        assert "name" in filter_obj.filter_fields
        assert "status" in filter_obj.filter_fields


class TestSearchFilter:
    """Test SearchFilter class."""
    
    def test_search_filter_creation(self):
        """Test creating a SearchFilter."""
        filter_obj = SearchFilter()
        assert filter_obj is not None
    
    def test_search_fields(self):
        """Test search fields configuration."""
        class MySearch(SearchFilter):
            search_fields = ["title", "description"]
        
        filter_obj = MySearch()
        assert "title" in filter_obj.search_fields
    
    def test_search_param(self):
        """Test search parameter name."""
        filter_obj = SearchFilter()
        assert filter_obj.search_param == "search"


class TestOrderingFilter:
    """Test OrderingFilter class."""
    
    def test_ordering_filter_creation(self):
        """Test creating an OrderingFilter."""
        filter_obj = OrderingFilter()
        assert filter_obj is not None
    
    def test_ordering_fields(self):
        """Test ordering fields configuration."""
        class MyOrdering(OrderingFilter):
            ordering_fields = ["created_at", "name"]
        
        filter_obj = MyOrdering()
        assert "created_at" in filter_obj.ordering_fields
    
    def test_default_ordering(self):
        """Test default ordering."""
        class MyOrdering(OrderingFilter):
            default_ordering = "-created_at"
        
        filter_obj = MyOrdering()
        assert filter_obj.default_ordering == "-created_at"
