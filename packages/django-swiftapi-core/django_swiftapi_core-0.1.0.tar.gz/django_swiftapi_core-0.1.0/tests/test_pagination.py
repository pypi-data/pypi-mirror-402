"""
Tests for SwiftAPI Pagination.
"""
import pytest
from swiftapi.pagination import (
    PageNumberPagination,
    LimitOffsetPagination,
    CursorPagination,
)


class TestPageNumberPagination:
    """Test PageNumberPagination."""
    
    def test_page_size_exists(self):
        """Test page size attribute exists."""
        paginator = PageNumberPagination()
        assert hasattr(paginator, 'page_size')
    
    def test_custom_page_size(self):
        """Test custom page size."""
        paginator = PageNumberPagination()
        paginator.page_size = 50
        assert paginator.page_size == 50
    
    def test_max_page_size_exists(self):
        """Test max page size attribute exists."""
        paginator = PageNumberPagination()
        assert hasattr(paginator, 'max_page_size')


class TestLimitOffsetPagination:
    """Test LimitOffsetPagination."""
    
    def test_default_limit_exists(self):
        """Test default limit attribute exists."""
        paginator = LimitOffsetPagination()
        assert hasattr(paginator, 'default_limit')
    
    def test_max_limit_exists(self):
        """Test max limit attribute exists."""
        paginator = LimitOffsetPagination()
        assert hasattr(paginator, 'max_limit')


class TestCursorPagination:
    """Test CursorPagination."""
    
    def test_page_size_exists(self):
        """Test page size attribute exists."""
        paginator = CursorPagination()
        assert hasattr(paginator, 'page_size')
    
    def test_ordering(self):
        """Test ordering field."""
        paginator = CursorPagination()
        paginator.ordering = "-created_at"
        assert paginator.ordering == "-created_at"
