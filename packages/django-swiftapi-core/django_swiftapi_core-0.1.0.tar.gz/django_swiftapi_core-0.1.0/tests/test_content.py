"""
Tests for SwiftAPI Content Negotiation.
"""
import pytest
from swiftapi.content import (
    JSONRenderer,
    CSVRenderer,
    XMLRenderer,
    HTMLRenderer,
    ContentNegotiator,
    JSONParser,
)


class TestRenderers:
    """Test renderer classes."""
    
    def test_json_renderer(self):
        """Test JSONRenderer."""
        renderer = JSONRenderer()
        assert renderer.media_type == "application/json"
        
        data = {"name": "John", "age": 30}
        result = renderer.render(data)
        
        assert b'"name"' in result
        assert b'"John"' in result
        assert b"30" in result
    
    def test_json_renderer_list(self):
        """Test JSONRenderer with list."""
        renderer = JSONRenderer()
        data = [{"id": 1}, {"id": 2}]
        result = renderer.render(data)
        
        assert b"[" in result
        assert b'"id"' in result
    
    def test_csv_renderer(self):
        """Test CSVRenderer."""
        renderer = CSVRenderer()
        assert renderer.media_type == "text/csv"
        
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        result = renderer.render(data)
        
        assert b"name" in result
        assert b"age" in result
        assert b"John" in result
    
    def test_xml_renderer(self):
        """Test XMLRenderer."""
        renderer = XMLRenderer()
        assert renderer.media_type == "application/xml"
        
        data = {"name": "John"}
        result = renderer.render(data)
        
        assert b"<" in result
        assert b">" in result
    
    def test_html_renderer(self):
        """Test HTMLRenderer."""
        renderer = HTMLRenderer()
        assert renderer.media_type == "text/html"


class TestParsers:
    """Test parser classes."""
    
    def test_json_parser(self):
        """Test JSONParser."""
        parser = JSONParser()
        assert parser.media_type == "application/json"
        
        stream = b'{"name": "John", "age": 30}'
        result = parser.parse(stream)
        
        assert result["name"] == "John"
        assert result["age"] == 30
    
    def test_json_parser_empty(self):
        """Test JSONParser with empty input."""
        parser = JSONParser()
        result = parser.parse(b"")
        assert result == {}


class TestContentNegotiator:
    """Test content negotiation."""
    
    def test_negotiator_creation(self):
        """Test creating ContentNegotiator."""
        negotiator = ContentNegotiator(
            renderers=[JSONRenderer(), CSVRenderer()]
        )
        assert negotiator is not None
    
    def test_negotiator_renderers(self):
        """Test negotiator has renderers."""
        negotiator = ContentNegotiator(
            renderers=[JSONRenderer(), CSVRenderer()]
        )
        assert len(negotiator.renderers) == 2
