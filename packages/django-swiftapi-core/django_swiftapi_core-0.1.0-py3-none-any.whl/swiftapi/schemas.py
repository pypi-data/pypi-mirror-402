"""
SwiftAPI Schema System.

Lightweight type-hint based validation and serialization that replaces
DRF's ModelSerializer with better performance and simpler syntax.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from swiftapi.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.models import Model

T = TypeVar("T", bound="Schema")


class FieldInfo:
    """
    Metadata container for schema field configuration.

    Used to store field-level options like read-only, write-only,
    default values, and validators.
    """

    def __init__(
        self,
        *,
        default: Any = ...,
        default_factory: Callable[[], Any] | None = None,
        required: bool = True,
        read_only: bool = False,
        write_only: bool = False,
        alias: str | None = None,
        description: str | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        pattern: str | None = None,
        validators: list[Callable[[Any], Any]] | None = None,
    ) -> None:
        self.default = default
        self.default_factory = default_factory
        self.required = required
        self.read_only = read_only
        self.write_only = write_only
        self.alias = alias
        self.description = description
        self.min_length = min_length
        self.max_length = max_length
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern
        self.validators = validators or []

    def has_default(self) -> bool:
        """Check if field has a default value."""
        return self.default is not ... or self.default_factory is not None

    def get_default(self) -> Any:
        """Get the default value for this field."""
        if self.default_factory is not None:
            return self.default_factory()
        return self.default


def Field(
    default: Any = ...,
    *,
    default_factory: Callable[[], Any] | None = None,
    required: bool = True,
    read_only: bool = False,
    write_only: bool = False,
    alias: str | None = None,
    description: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    pattern: str | None = None,
    validators: list[Callable[[Any], Any]] | None = None,
) -> Any:
    """
    Define field metadata for a schema field.

    Example:
        class UserSchema(Schema):
            name: str = Field(min_length=1, max_length=100)
            email: str = Field(description="User email address")
            password: str = Field(write_only=True)
            id: int = Field(read_only=True)

    Args:
        default: Default value for the field
        default_factory: Callable that returns default value
        required: Whether field is required (default True)
        read_only: Only include in output, not input
        write_only: Only accept in input, not output
        alias: Alternative name for the field in input/output
        description: Field description for documentation
        min_length: Minimum length for strings
        max_length: Maximum length for strings
        min_value: Minimum value for numbers
        max_value: Maximum value for numbers
        pattern: Regex pattern for string validation
        validators: List of additional validator functions

    Returns:
        FieldInfo with the specified configuration
    """
    return FieldInfo(
        default=default,
        default_factory=default_factory,
        required=required,
        read_only=read_only,
        write_only=write_only,
        alias=alias,
        description=description,
        min_length=min_length,
        max_length=max_length,
        min_value=min_value,
        max_value=max_value,
        pattern=pattern,
        validators=validators,
    )


class SchemaMeta(type):
    """
    Metaclass for Schema that processes type hints and field definitions.

    This metaclass:
    1. Extracts type hints from the class
    2. Processes FieldInfo annotations
    3. Caches field information for fast validation
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip processing for the base Schema class
        if name == "Schema" and not bases:
            return cls

        # Process fields from type hints and annotations
        cls._fields = {}  # type: ignore
        cls._read_only_fields = set()  # type: ignore
        cls._write_only_fields = set()  # type: ignore

        # Collect hints from all parent classes
        all_hints: dict[str, Any] = {}
        for base in reversed(cls.__mro__):
            if hasattr(base, "__annotations__"):
                try:
                    hints = get_type_hints(base) if base.__module__ != "builtins" else {}
                except Exception:
                    hints = getattr(base, "__annotations__", {})
                all_hints.update(hints)

        for field_name, field_type in all_hints.items():
            if field_name.startswith("_"):
                continue

            # Get field info from class attribute or create default
            field_info = namespace.get(field_name)
            if not isinstance(field_info, FieldInfo):
                if field_info is not None and field_info is not ...:
                    # Value is a default, wrap it
                    field_info = FieldInfo(default=field_info)
                else:
                    # Check if Optional (has None in union)
                    is_optional = _is_optional_type(field_type)
                    field_info = FieldInfo(required=not is_optional)

            cls._fields[field_name] = (field_type, field_info)  # type: ignore

            if field_info.read_only:
                cls._read_only_fields.add(field_name)  # type: ignore
            if field_info.write_only:
                cls._write_only_fields.add(field_name)  # type: ignore

        return cls


def _is_optional_type(type_hint: Any) -> bool:
    """Check if a type hint is Optional (Union with None)."""
    origin = get_origin(type_hint)
    if origin is Union:
        args = get_args(type_hint)
        return type(None) in args
    return False


def _get_inner_type(type_hint: Any) -> Any:
    """Get the inner type from Optional or other wrappers."""
    origin = get_origin(type_hint)
    if origin is Union:
        args = get_args(type_hint)
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
        return type_hint
    return type_hint


class Schema(metaclass=SchemaMeta):
    """
    Base class for data validation and serialization schemas.

    Schemas use Python type hints for field definitions and provide:
    - Single-pass O(n) validation
    - Nested schema support
    - Model instance serialization
    - Read/write-only field handling

    Example:
        class UserSchema(Schema):
            id: int = Field(read_only=True)
            email: str
            name: str = Field(min_length=1, max_length=100)
            password: str = Field(write_only=True)
            is_active: bool = True

        # Validate input data
        data = {"email": "user@example.com", "name": "John", "password": "secret"}
        validated = UserSchema.validate(data)

        # Serialize model instance
        user = User.objects.get(pk=1)
        output = UserSchema.serialize(user)
    """

    _fields: ClassVar[dict[str, tuple[Any, FieldInfo]]]
    _read_only_fields: ClassVar[set[str]]
    _write_only_fields: ClassVar[set[str]]

    class Meta:
        """Schema configuration."""
        model: type[Model] | None = None
        fields: list[str] | Literal["__all__"] | None = None
        exclude: list[str] | None = None
        read_only_fields: list[str] | None = None
        extra_fields: dict[str, Any] | None = None

    def __init__(self, **data: Any) -> None:
        """
        Initialize schema with data.

        Args:
            **data: Field values
        """
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def validate(
        cls: type[T],
        data: dict[str, Any],
        *,
        partial: bool = False,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate input data against the schema.

        Performs single-pass validation for O(n) complexity.

        Args:
            data: Input data dictionary
            partial: If True, skip required field checks (for PATCH)
            context: Optional context data for validators

        Returns:
            Validated data dictionary

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("Expected a dictionary for input data.")

        errors: dict[str, list[str]] = {}
        validated: dict[str, Any] = {}

        for field_name, (field_type, field_info) in cls._fields.items():
            # Skip read-only fields in input
            if field_info.read_only:
                continue

            # Get value using alias or field name
            input_key = field_info.alias or field_name

            if input_key in data:
                raw_value = data[input_key]

                try:
                    # Type coercion and validation
                    value = cls._validate_field(
                        field_name, field_type, field_info, raw_value, context
                    )
                    validated[field_name] = value
                except ValidationError as e:
                    errors[field_name] = [str(e.detail)]
                except (TypeError, ValueError) as e:
                    errors[field_name] = [str(e)]

            elif field_info.has_default():
                # Apply default value
                validated[field_name] = field_info.get_default()

            elif field_info.required and not partial:
                errors[field_name] = ["This field is required."]

        # Check for unknown fields
        known_keys = {
            field_info.alias or name
            for name, (_, field_info) in cls._fields.items()
            if not field_info.read_only
        }
        unknown_keys = set(data.keys()) - known_keys
        for key in unknown_keys:
            errors[key] = ["Unknown field."]

        if errors:
            raise ValidationError(errors)

        return validated

    @classmethod
    def _validate_field(
        cls,
        field_name: str,
        field_type: Any,
        field_info: FieldInfo,
        value: Any,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Validate and coerce a single field value.

        Args:
            field_name: Name of the field
            field_type: Expected type
            field_info: Field configuration
            value: Raw input value
            context: Validation context

        Returns:
            Validated and coerced value
        """
        # Handle None for optional fields
        if value is None:
            if _is_optional_type(field_type):
                return None
            raise ValidationError("This field may not be null.", field=field_name)

        # Get the actual type (unwrap Optional)
        actual_type = _get_inner_type(field_type)
        origin = get_origin(actual_type)

        # Handle nested schemas
        if isinstance(actual_type, type) and issubclass(actual_type, Schema):
            if isinstance(value, dict):
                return actual_type.validate(value, context=context)
            raise ValidationError(
                f"Expected object for nested schema, got {type(value).__name__}",
                field=field_name,
            )

        # Handle lists
        if origin is list:
            if not isinstance(value, list):
                raise ValidationError(f"Expected list, got {type(value).__name__}")

            args = get_args(actual_type)
            if args:
                item_type = args[0]
                result = []
                for _i, item in enumerate(value):
                    if isinstance(item_type, type) and issubclass(item_type, Schema):
                        result.append(item_type.validate(item, context=context))
                    else:
                        result.append(cls._coerce_value(item, item_type, field_name))
                return result
            return value

        # Handle dicts
        if origin is dict:
            if not isinstance(value, dict):
                raise ValidationError(f"Expected object, got {type(value).__name__}")
            return value

        # Handle enums
        if isinstance(actual_type, type) and issubclass(actual_type, Enum):
            if isinstance(value, actual_type):
                return value
            try:
                return actual_type(value)
            except ValueError:
                valid_values = [e.value for e in actual_type]
                raise ValidationError(
                    f"Invalid value. Must be one of: {valid_values}"
                )

        # Coerce to basic types
        value = cls._coerce_value(value, actual_type, field_name)

        # Apply field-level validations
        cls._apply_field_validations(field_name, field_info, value)

        # Run custom validators
        for validator in field_info.validators:
            value = validator(value)

        return value

    @classmethod
    def _coerce_value(cls, value: Any, target_type: Any, field_name: str) -> Any:
        """
        Coerce a value to the target type.

        Args:
            value: Input value
            target_type: Target type
            field_name: Field name for error messages

        Returns:
            Coerced value
        """
        # Already correct type
        if isinstance(value, target_type):
            return value

        # String coercion
        if target_type is str:
            return str(value)

        # Integer coercion
        if target_type is int:
            if isinstance(value, bool):
                raise ValidationError(
                    "Expected integer, got boolean", field=field_name
                )
            if isinstance(value, float) and not value.is_integer():
                raise ValidationError(
                    "Expected integer, got float", field=field_name
                )
            try:
                return int(value)
            except (TypeError, ValueError):
                raise ValidationError(
                    "Cannot convert to integer", field=field_name
                )

        # Float coercion
        if target_type is float:
            try:
                return float(value)
            except (TypeError, ValueError):
                raise ValidationError("Cannot convert to float", field=field_name)

        # Boolean coercion (strict)
        if target_type is bool:
            if isinstance(value, bool):
                return value
            if value in (1, "1", "true", "True", "TRUE"):
                return True
            if value in (0, "0", "false", "False", "FALSE"):
                return False
            raise ValidationError(
                f"Expected boolean, got {type(value).__name__}", field=field_name
            )

        # Decimal coercion
        if target_type is Decimal:
            try:
                return Decimal(str(value))
            except Exception:
                raise ValidationError("Cannot convert to decimal", field=field_name)

        # UUID coercion
        if target_type is uuid.UUID:
            if isinstance(value, uuid.UUID):
                return value
            try:
                return uuid.UUID(str(value))
            except Exception:
                raise ValidationError("Invalid UUID format", field=field_name)

        # Datetime coercion
        if target_type is datetime.datetime:
            if isinstance(value, datetime.datetime):
                return value
            if isinstance(value, str):
                try:
                    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    raise ValidationError(
                        "Invalid datetime format. Use ISO 8601.", field=field_name
                    )
            raise ValidationError("Cannot convert to datetime", field=field_name)

        # Date coercion
        if target_type is datetime.date:
            if isinstance(value, datetime.date):
                return value
            if isinstance(value, str):
                try:
                    return datetime.date.fromisoformat(value)
                except ValueError:
                    raise ValidationError(
                        "Invalid date format. Use YYYY-MM-DD.", field=field_name
                    )
            raise ValidationError("Cannot convert to date", field=field_name)

        # Time coercion
        if target_type is datetime.time:
            if isinstance(value, datetime.time):
                return value
            if isinstance(value, str):
                try:
                    return datetime.time.fromisoformat(value)
                except ValueError:
                    raise ValidationError(
                        "Invalid time format. Use HH:MM:SS.", field=field_name
                    )
            raise ValidationError("Cannot convert to time", field=field_name)

        # Default: return as-is
        return value

    @classmethod
    def _apply_field_validations(
        cls,
        field_name: str,
        field_info: FieldInfo,
        value: Any,
    ) -> None:
        """Apply field-level validation rules."""
        # String length validations
        if isinstance(value, str):
            if field_info.min_length is not None and len(value) < field_info.min_length:
                raise ValidationError(
                    f"Minimum length is {field_info.min_length} characters.",
                    field=field_name,
                )
            if field_info.max_length is not None and len(value) > field_info.max_length:
                raise ValidationError(
                    f"Maximum length is {field_info.max_length} characters.",
                    field=field_name,
                )
            if field_info.pattern is not None:
                import re
                if not re.match(field_info.pattern, value):
                    raise ValidationError(
                        "Value does not match required pattern.",
                        field=field_name,
                    )

        # Numeric validations
        if isinstance(value, (int, float, Decimal)):
            if field_info.min_value is not None and value < field_info.min_value:
                raise ValidationError(
                    f"Minimum value is {field_info.min_value}.",
                    field=field_name,
                )
            if field_info.max_value is not None and value > field_info.max_value:
                raise ValidationError(
                    f"Maximum value is {field_info.max_value}.",
                    field=field_name,
                )

    @classmethod
    def serialize(
        cls,
        instance: Any,
        *,
        many: bool = False,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Serialize a model instance or list of instances.

        Args:
            instance: Model instance or iterable of instances
            many: If True, serialize multiple instances
            context: Optional context data

        Returns:
            Serialized dictionary or list of dictionaries
        """
        if many:
            return [cls._serialize_one(item, context) for item in instance]
        return cls._serialize_one(instance, context)

    @classmethod
    def _serialize_one(
        cls,
        instance: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Serialize a single instance."""
        result: dict[str, Any] = {}

        for field_name, (field_type, field_info) in cls._fields.items():
            # Skip write-only fields in output
            if field_info.write_only:
                continue

            # Get value from instance
            if isinstance(instance, dict):
                value = instance.get(field_name)
            else:
                value = getattr(instance, field_name, None)

            # Serialize nested schemas
            actual_type = _get_inner_type(field_type)
            if isinstance(actual_type, type) and issubclass(actual_type, Schema):
                if value is not None:
                    value = actual_type.serialize(value, context=context)
            elif get_origin(actual_type) is list:
                args = get_args(actual_type)
                if args and isinstance(args[0], type) and issubclass(args[0], Schema):
                    if value is not None:
                        value = args[0].serialize(value, many=True, context=context)

            # Convert special types
            value = cls._serialize_value(value)

            # Use alias for output key
            output_key = field_info.alias or field_name
            result[output_key] = value

        return result

    @classmethod
    def _serialize_value(cls, value: Any) -> Any:
        """Convert special types to JSON-serializable values."""
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, datetime.date):
            return value.isoformat()
        if isinstance(value, datetime.time):
            return value.isoformat()
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, (list, tuple)):
            return [cls._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: cls._serialize_value(v) for k, v in value.items()}
        return value

    @classmethod
    def from_model(
        cls: type[T],
        model: type[Model],
        *,
        fields: list[str] | Literal["__all__"] | None = None,
        exclude: list[str] | None = None,
        read_only_fields: list[str] | None = None,
    ) -> type[T]:
        """
        Create a schema from a Django model.

        Args:
            model: Django model class
            fields: Fields to include (or "__all__" for all)
            exclude: Fields to exclude
            read_only_fields: Fields that are read-only

        Returns:
            New Schema subclass
        """

        exclude = exclude or []
        read_only_fields = read_only_fields or []

        # Get model fields
        model_fields = {f.name: f for f in model._meta.get_fields()}

        # Determine which fields to include
        if fields == "__all__":
            include_fields = [
                name for name in model_fields
                if name not in exclude
            ]
        elif fields:
            include_fields = [f for f in fields if f not in exclude]
        else:
            include_fields = [
                name for name, f in model_fields.items()
                if name not in exclude and hasattr(f, "column")
            ]

        # Build type hints and field infos
        annotations: dict[str, Any] = {}
        namespace: dict[str, Any] = {}

        for field_name in include_fields:
            field = model_fields.get(field_name)
            if field is None:
                continue

            # Map Django field to Python type
            python_type = _django_field_to_python_type(field)
            is_nullable = getattr(field, "null", False)

            if is_nullable:
                python_type = python_type | None

            annotations[field_name] = python_type

            # Create FieldInfo
            is_read_only = (
                field_name in read_only_fields
                or field_name == "id"
                or getattr(field, "primary_key", False)
            )
            has_default = getattr(field, "default", None) is not None

            namespace[field_name] = FieldInfo(
                read_only=is_read_only,
                required=not is_nullable and not has_default and not is_read_only,
            )

        # Create new schema class
        namespace["__annotations__"] = annotations
        namespace["__module__"] = cls.__module__

        schema_name = f"{model.__name__}Schema"
        return SchemaMeta(schema_name, (cls,), namespace)  # type: ignore


def _django_field_to_python_type(field: Any) -> type:
    """Map a Django field to a Python type."""
    from django.db import models

    type_mapping: dict[type, type] = {
        models.AutoField: int,
        models.BigAutoField: int,
        models.SmallAutoField: int,
        models.IntegerField: int,
        models.SmallIntegerField: int,
        models.BigIntegerField: int,
        models.PositiveIntegerField: int,
        models.PositiveSmallIntegerField: int,
        models.PositiveBigIntegerField: int,
        models.FloatField: float,
        models.DecimalField: Decimal,
        models.CharField: str,
        models.TextField: str,
        models.EmailField: str,
        models.URLField: str,
        models.SlugField: str,
        models.UUIDField: uuid.UUID,
        models.BooleanField: bool,
        models.DateField: datetime.date,
        models.DateTimeField: datetime.datetime,
        models.TimeField: datetime.time,
        models.JSONField: dict,
    }

    for django_type, python_type in type_mapping.items():
        if isinstance(field, django_type):
            return python_type

    # Default to Any for unknown types
    return Any  # type: ignore


# Validator decorator
def validator(*fields: str, pre: bool = False):
    """
    Decorator to create field validators.

    Args:
        *fields: Field names to validate
        pre: If True, run before type coercion

    Example:
        class UserSchema(Schema):
            email: str

            @validator("email")
            def validate_email(cls, value):
                if "@" not in value:
                    raise ValueError("Invalid email format")
                return value.lower()
    """
    def decorator(func: Callable) -> Callable:
        func._validator_fields = fields  # type: ignore
        func._validator_pre = pre  # type: ignore
        return classmethod(func)
    return decorator
