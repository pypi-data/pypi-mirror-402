"""
Tests for SwiftAPI Responses.
"""
import pytest
import json
from swiftapi.responses import (
    Response,
    SuccessResponse,
    CreatedResponse,
    NoContentResponse,
    ErrorResponse,
    PaginatedResponse,
)


class TestResponses:
    """Test response classes."""
    
    def test_success_response(self):
        """Test SuccessResponse."""
        response = SuccessResponse(data={"name": "John"})
        assert response.status_code == 200
        
        content = json.loads(response.content)
        assert content["data"]["name"] == "John"
    
    def test_created_response(self):
        """Test CreatedResponse."""
        response = CreatedResponse(data={"id": 1, "name": "New Item"})
        assert response.status_code == 201
        
        content = json.loads(response.content)
        assert content["data"]["id"] == 1
    
    def test_no_content_response(self):
        """Test NoContentResponse."""
        response = NoContentResponse()
        assert response.status_code == 204
        assert response.content == b""
    
    def test_error_response(self):
        """Test ErrorResponse."""
        response = ErrorResponse(
            message="Something went wrong",
            code="server_error",
            status=500,
        )
        assert response.status_code == 500
        
        content = json.loads(response.content)
        assert content["error"]["message"] == "Something went wrong"
        assert content["error"]["code"] == "server_error"
    
    def test_paginated_response(self):
        """Test PaginatedResponse."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse(
            results=items,
            count=100,
            next_url="/api/items/?page=2",
            previous_url=None,
        )
        assert response.status_code == 200
        
        content = json.loads(response.content)
        # PaginatedResponse wraps everything in 'data'
        data = content.get("data", content)
        assert data["count"] == 100
        assert len(data["results"]) == 3
        assert data["next"] == "/api/items/?page=2"
        assert data["previous"] is None


class TestResponseHeaders:
    """Test response headers."""
    
    def test_content_type_json(self):
        """Test that responses have JSON content type."""
        response = SuccessResponse(data={})
        assert "application/json" in response["Content-Type"]
