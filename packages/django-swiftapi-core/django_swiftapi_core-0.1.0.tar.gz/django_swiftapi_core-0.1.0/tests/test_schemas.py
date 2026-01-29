"""
Tests for SwiftAPI Schema system.
"""
import pytest
from swiftapi.schemas import Schema
from swiftapi.fields import (
    CharField, IntegerField, EmailField, BooleanField,
    DateTimeField, DecimalField, ChoiceField, ListField
)
from swiftapi.exceptions import ValidationError


class TestBasicSchema:
    """Test basic schema validation."""
    
    def test_schema_definition(self):
        """Test that schemas can be defined with type hints."""
        class UserSchema(Schema):
            name: str
            age: int
            email: str
        
        assert hasattr(UserSchema, '__annotations__')
        assert 'name' in UserSchema.__annotations__
    
    def test_schema_validation_valid(self):
        """Test schema validation with valid data."""
        class UserSchema(Schema):
            name: str
            age: int
        
        data = {"name": "John", "age": 30}
        schema = UserSchema()
        result = schema.validate(data)
        
        assert result["name"] == "John"
        assert result["age"] == 30
    
    def test_schema_validation_missing_field(self):
        """Test schema validation with missing required field."""
        class UserSchema(Schema):
            name: str
            age: int
        
        data = {"name": "John"}  # missing age
        schema = UserSchema()
        
        with pytest.raises(ValidationError):
            schema.validate(data)


class TestFieldTypes:
    """Test individual field types."""
    
    def test_char_field(self):
        """Test CharField validation."""
        field = CharField(max_length=10)
        result = field.run_validation("hello")
        assert result == "hello"
    
    def test_char_field_max_length(self):
        """Test CharField max_length validation."""
        field = CharField(max_length=5)
        with pytest.raises(ValidationError):
            field.run_validation("hello world")
    
    def test_email_field_valid(self):
        """Test EmailField with valid email."""
        field = EmailField()
        result = field.run_validation("test@example.com")
        assert result == "test@example.com"
    
    def test_email_field_invalid(self):
        """Test EmailField with invalid email."""
        field = EmailField()
        with pytest.raises(ValidationError):
            field.run_validation("not-an-email")
    
    def test_integer_field(self):
        """Test IntegerField validation."""
        field = IntegerField(min_value=0, max_value=100)
        assert field.run_validation(50) == 50
    
    def test_integer_field_out_of_range(self):
        """Test IntegerField out of range."""
        field = IntegerField(max_value=10)
        with pytest.raises(ValidationError):
            field.run_validation(100)
    
    def test_boolean_field(self):
        """Test BooleanField validation."""
        field = BooleanField()
        assert field.run_validation(True) is True
        assert field.run_validation("true") is True
        assert field.run_validation("false") is False
        assert field.run_validation(0) is False
    
    def test_choice_field(self):
        """Test ChoiceField validation."""
        field = ChoiceField(choices=["red", "green", "blue"])
        assert field.run_validation("red") == "red"
    
    def test_choice_field_invalid(self):
        """Test ChoiceField with invalid choice."""
        field = ChoiceField(choices=["red", "green", "blue"])
        with pytest.raises(ValidationError):
            field.run_validation("yellow")
    
    def test_list_field(self):
        """Test ListField validation."""
        field = ListField(child=IntegerField())
        result = field.run_validation([1, 2, 3])
        assert result == [1, 2, 3]


class TestSchemaSerializer:
    """Test schema serialization."""
    
    def test_serialize_dict(self):
        """Test serializing a dictionary."""
        class ProductSchema(Schema):
            name: str
            price: float
        
        schema = ProductSchema()
        data = {"name": "Widget", "price": 9.99, "extra": "ignored"}
        result = schema.serialize(data)
        
        assert "name" in result
        assert "price" in result
