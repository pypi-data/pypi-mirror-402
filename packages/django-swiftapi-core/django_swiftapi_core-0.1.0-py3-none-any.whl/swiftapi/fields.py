"""
SwiftAPI Field Types.

Comprehensive field types for schema validation - similar to DRF's fields.py.
"""

from __future__ import annotations

import datetime
import decimal
import ipaddress
import re
import uuid
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from swiftapi.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable
    pass

T = TypeVar("T")


class Empty:
    """Represents an empty/missing value (distinct from None)."""
    pass


empty = Empty()


class Field(Generic[T]):
    """
    Base field class for schema validation.

    All field types inherit from this base class.
    """

    default_error_messages = {
        "required": "This field is required.",
        "null": "This field may not be null.",
        "invalid": "Invalid value.",
    }

    def __init__(
        self,
        *,
        read_only: bool = False,
        write_only: bool = False,
        required: bool = True,
        default: Any = empty,
        allow_null: bool = False,
        source: str | None = None,
        validators: list[Callable] | None = None,
        error_messages: dict[str, str] | None = None,
        label: str | None = None,
        help_text: str | None = None,
    ) -> None:
        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.allow_null = allow_null
        self.source = source
        self.validators = validators or []
        self.label = label
        self.help_text = help_text
        self.field_name: str | None = None
        self.parent: Any = None

        # Merge error messages
        self.error_messages = {**self.default_error_messages}
        if error_messages:
            self.error_messages.update(error_messages)

    def bind(self, field_name: str, parent: Any) -> None:
        """Bind field to a schema instance."""
        self.field_name = field_name
        self.parent = parent
        if self.source is None:
            self.source = field_name

    def run_validation(self, data: Any) -> T:
        """Run field validation."""
        # Handle empty/missing values
        if data is empty:
            if self.required:
                self.fail("required")
            return self.get_default()

        # Handle null values
        if data is None:
            if not self.allow_null:
                self.fail("null")
            return None  # type: ignore

        # Validate and convert
        value = self.to_internal_value(data)

        # Run validators
        self.run_validators(value)

        return value

    def to_internal_value(self, data: Any) -> T:
        """Convert input data to internal Python value."""
        raise NotImplementedError()

    def to_representation(self, value: T) -> Any:
        """Convert internal value to output representation."""
        return value

    def get_default(self) -> T:
        """Get the default value."""
        if self.default is empty:
            raise ValidationError({self.field_name or "field": "This field is required."})
        if callable(self.default):
            return self.default()
        return self.default

    def run_validators(self, value: T) -> None:
        """Run all registered validators."""
        errors = []
        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as e:
                errors.append(str(e))
        if errors:
            raise ValidationError({self.field_name or "field": errors})

    def fail(self, key: str, **kwargs: Any) -> None:
        """Raise a validation error with a specific message."""
        msg = self.error_messages.get(key, key)
        if kwargs:
            msg = msg.format(**kwargs)
        raise ValidationError({self.field_name or "field": msg})


# =============================================================================
# Boolean Fields
# =============================================================================

class BooleanField(Field[bool]):
    """Boolean field that handles various truthy/falsy values."""

    TRUE_VALUES = {"t", "T", "true", "True", "TRUE", "1", 1}
    FALSE_VALUES = {"f", "F", "false", "False", "FALSE", "0", 0}
    NULL_VALUES = {"n", "N", "null", "Null", "NULL", "", None}

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Must be a valid boolean.",
    }

    def to_internal_value(self, data: Any) -> bool:
        if data in self.TRUE_VALUES:
            return True
        if data in self.FALSE_VALUES:
            return False
        if data in self.NULL_VALUES and self.allow_null:
            return None  # type: ignore
        self.fail("invalid")
        return False  # Never reached


class NullBooleanField(BooleanField):
    """Boolean field that allows null values."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["allow_null"] = True
        super().__init__(**kwargs)


# =============================================================================
# String Fields
# =============================================================================

class CharField(Field[str]):
    """String field with length validation."""

    default_error_messages = {
        **Field.default_error_messages,
        "blank": "This field may not be blank.",
        "max_length": "Ensure this field has no more than {max_length} characters.",
        "min_length": "Ensure this field has at least {min_length} characters.",
    }

    def __init__(
        self,
        *,
        max_length: int | None = None,
        min_length: int | None = None,
        allow_blank: bool = False,
        trim_whitespace: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
        self.allow_blank = allow_blank
        self.trim_whitespace = trim_whitespace

    def to_internal_value(self, data: Any) -> str:
        if not isinstance(data, str):
            data = str(data)

        if self.trim_whitespace:
            data = data.strip()

        if not data and not self.allow_blank:
            self.fail("blank")

        if self.max_length is not None and len(data) > self.max_length:
            self.fail("max_length", max_length=self.max_length)

        if self.min_length is not None and len(data) < self.min_length:
            self.fail("min_length", min_length=self.min_length)

        return data


class TextField(CharField):
    """Text field for longer content (alias for CharField)."""
    pass


class EmailField(CharField):
    """Email address field with validation."""

    default_error_messages = {
        **CharField.default_error_messages,
        "invalid": "Enter a valid email address.",
    }

    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", 254)
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data)
        if value and not self.EMAIL_REGEX.match(value):
            self.fail("invalid")
        return value.lower()


class URLField(CharField):
    """URL field with validation."""

    default_error_messages = {
        **CharField.default_error_messages,
        "invalid": "Enter a valid URL.",
    }

    URL_REGEX = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", 2000)
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data)
        if value and not self.URL_REGEX.match(value):
            self.fail("invalid")
        return value


class SlugField(CharField):
    """Slug field (lowercase letters, numbers, hyphens, underscores)."""

    default_error_messages = {
        **CharField.default_error_messages,
        "invalid": "Enter a valid 'slug' (letters, numbers, hyphens, underscores).",
    }

    SLUG_REGEX = re.compile(r"^[-a-zA-Z0-9_]+$")

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", 50)
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data)
        if value and not self.SLUG_REGEX.match(value):
            self.fail("invalid")
        return value


class UUIDField(Field[uuid.UUID]):
    """UUID field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Must be a valid UUID.",
    }

    def __init__(self, *, format: str = "hex_verbose", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.uuid_format = format  # 'hex_verbose', 'hex', 'int', 'urn'

    def to_internal_value(self, data: Any) -> uuid.UUID:
        if isinstance(data, uuid.UUID):
            return data
        try:
            if isinstance(data, int):
                return uuid.UUID(int=data)
            return uuid.UUID(str(data))
        except (ValueError, AttributeError):
            self.fail("invalid")
            return uuid.uuid4()  # Never reached

    def to_representation(self, value: uuid.UUID) -> str:
        if self.uuid_format == "hex":
            return value.hex
        if self.uuid_format == "int":
            return str(value.int)
        if self.uuid_format == "urn":
            return value.urn
        return str(value)


class IPAddressField(CharField):
    """IP address field (IPv4 or IPv6)."""

    default_error_messages = {
        **CharField.default_error_messages,
        "invalid": "Enter a valid IP address.",
    }

    def __init__(self, *, protocol: str = "both", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.protocol = protocol  # 'both', 'IPv4', 'IPv6'

    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data)
        try:
            addr = ipaddress.ip_address(value)
            if self.protocol == "IPv4" and addr.version != 4:
                self.fail("invalid")
            if self.protocol == "IPv6" and addr.version != 6:
                self.fail("invalid")
            return str(addr)
        except ValueError:
            self.fail("invalid")
            return ""  # Never reached


class RegexField(CharField):
    """Field validated against a regex pattern."""

    def __init__(self, regex: str | re.Pattern, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if isinstance(regex, str):
            regex = re.compile(regex)
        self.regex = regex

    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data)
        if value and not self.regex.search(value):
            self.fail("invalid")
        return value


# =============================================================================
# Numeric Fields
# =============================================================================

class IntegerField(Field[int]):
    """Integer field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "A valid integer is required.",
        "max_value": "Ensure this value is less than or equal to {max_value}.",
        "min_value": "Ensure this value is greater than or equal to {min_value}.",
    }

    def __init__(
        self,
        *,
        max_value: int | None = None,
        min_value: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.max_value = max_value
        self.min_value = min_value

    def to_internal_value(self, data: Any) -> int:
        try:
            value = int(data)
        except (ValueError, TypeError):
            self.fail("invalid")
            return 0  # Never reached

        if self.max_value is not None and value > self.max_value:
            self.fail("max_value", max_value=self.max_value)

        if self.min_value is not None and value < self.min_value:
            self.fail("min_value", min_value=self.min_value)

        return value


class FloatField(Field[float]):
    """Float field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "A valid number is required.",
        "max_value": "Ensure this value is less than or equal to {max_value}.",
        "min_value": "Ensure this value is greater than or equal to {min_value}.",
    }

    def __init__(
        self,
        *,
        max_value: float | None = None,
        min_value: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.max_value = max_value
        self.min_value = min_value

    def to_internal_value(self, data: Any) -> float:
        try:
            value = float(data)
        except (ValueError, TypeError):
            self.fail("invalid")
            return 0.0  # Never reached

        if self.max_value is not None and value > self.max_value:
            self.fail("max_value", max_value=self.max_value)

        if self.min_value is not None and value < self.min_value:
            self.fail("min_value", min_value=self.min_value)

        return value


class DecimalField(Field[decimal.Decimal]):
    """Decimal field with precision control."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "A valid number is required.",
        "max_value": "Ensure this value is less than or equal to {max_value}.",
        "min_value": "Ensure this value is greater than or equal to {min_value}.",
        "max_digits": "Ensure that there are no more than {max_digits} digits in total.",
        "max_decimal_places": "Ensure that there are no more than {max_decimal_places} decimal places.",
        "max_whole_digits": "Ensure that there are no more than {max_whole_digits} digits before the decimal point.",
    }

    def __init__(
        self,
        max_digits: int,
        decimal_places: int,
        *,
        coerce_to_string: bool = False,
        max_value: decimal.Decimal | None = None,
        min_value: decimal.Decimal | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.coerce_to_string = coerce_to_string
        self.max_value = max_value
        self.min_value = min_value

    def to_internal_value(self, data: Any) -> decimal.Decimal:
        try:
            value = decimal.Decimal(str(data))
        except (decimal.InvalidOperation, ValueError, TypeError):
            self.fail("invalid")
            return decimal.Decimal(0)  # Never reached

        if value.is_nan():
            self.fail("invalid")

        # Validate digits
        _sign, digits, exp = value.as_tuple()
        whole_digits = len(digits) + exp

        if whole_digits > self.max_digits - self.decimal_places:
            self.fail("max_whole_digits", max_whole_digits=self.max_digits - self.decimal_places)

        if -exp > self.decimal_places:
            self.fail("max_decimal_places", max_decimal_places=self.decimal_places)

        if len(digits) > self.max_digits:
            self.fail("max_digits", max_digits=self.max_digits)

        if self.max_value is not None and value > self.max_value:
            self.fail("max_value", max_value=self.max_value)

        if self.min_value is not None and value < self.min_value:
            self.fail("min_value", min_value=self.min_value)

        return value

    def to_representation(self, value: decimal.Decimal) -> str | decimal.Decimal:
        if self.coerce_to_string:
            return str(value.quantize(decimal.Decimal(10) ** -self.decimal_places))
        return value


# =============================================================================
# Date/Time Fields
# =============================================================================

class DateTimeField(Field[datetime.datetime]):
    """DateTime field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Datetime has wrong format. Use ISO 8601 format.",
    }

    def __init__(
        self,
        *,
        format: str | None = None,
        input_formats: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format or "%Y-%m-%dT%H:%M:%S"
        self.input_formats = input_formats or [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

    def to_internal_value(self, data: Any) -> datetime.datetime:
        if isinstance(data, datetime.datetime):
            return data
        if isinstance(data, datetime.date):
            return datetime.datetime(data.year, data.month, data.day)

        if not isinstance(data, str):
            self.fail("invalid")

        for fmt in self.input_formats:
            try:
                return datetime.datetime.strptime(data, fmt)
            except ValueError:
                continue

        self.fail("invalid")
        return datetime.datetime.now()  # Never reached

    def to_representation(self, value: datetime.datetime) -> str:
        return value.strftime(self.format)


class DateField(Field[datetime.date]):
    """Date field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Date has wrong format. Use YYYY-MM-DD.",
    }

    def __init__(
        self,
        *,
        format: str | None = None,
        input_formats: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format or "%Y-%m-%d"
        self.input_formats = input_formats or ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]

    def to_internal_value(self, data: Any) -> datetime.date:
        if isinstance(data, datetime.date):
            return data
        if isinstance(data, datetime.datetime):
            return data.date()

        if not isinstance(data, str):
            self.fail("invalid")

        for fmt in self.input_formats:
            try:
                return datetime.datetime.strptime(data, fmt).date()
            except ValueError:
                continue

        self.fail("invalid")
        return datetime.date.today()  # Never reached

    def to_representation(self, value: datetime.date) -> str:
        return value.strftime(self.format)


class TimeField(Field[datetime.time]):
    """Time field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Time has wrong format. Use HH:MM:SS.",
    }

    def __init__(
        self,
        *,
        format: str | None = None,
        input_formats: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format or "%H:%M:%S"
        self.input_formats = input_formats or ["%H:%M:%S", "%H:%M"]

    def to_internal_value(self, data: Any) -> datetime.time:
        if isinstance(data, datetime.time):
            return data

        if not isinstance(data, str):
            self.fail("invalid")

        for fmt in self.input_formats:
            try:
                return datetime.datetime.strptime(data, fmt).time()
            except ValueError:
                continue

        self.fail("invalid")
        return datetime.time()  # Never reached

    def to_representation(self, value: datetime.time) -> str:
        return value.strftime(self.format)


class DurationField(Field[datetime.timedelta]):
    """Duration/timedelta field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Duration has wrong format. Use [DD] [HH:[MM:]]ss[.uuuuuu].",
    }

    def to_internal_value(self, data: Any) -> datetime.timedelta:
        if isinstance(data, datetime.timedelta):
            return data

        if isinstance(data, (int, float)):
            return datetime.timedelta(seconds=data)

        if isinstance(data, str):
            # Parse ISO 8601 duration or seconds
            try:
                return datetime.timedelta(seconds=float(data))
            except ValueError:
                pass

        self.fail("invalid")
        return datetime.timedelta()  # Never reached

    def to_representation(self, value: datetime.timedelta) -> float:
        return value.total_seconds()


# =============================================================================
# Choice Fields
# =============================================================================

class ChoiceField(Field[str]):
    """Choice field with predefined options."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid_choice": '"{input}" is not a valid choice.',
    }

    def __init__(
        self,
        choices: list[tuple[Any, str]] | list[str],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        # Normalize choices to (value, display) tuples
        self.choices = []
        for choice in choices:
            if isinstance(choice, tuple):
                self.choices.append(choice)
            else:
                self.choices.append((choice, choice))
        self._choice_values = {c[0] for c in self.choices}

    def to_internal_value(self, data: Any) -> str:
        if data in self._choice_values:
            return data

        # Try string comparison
        str_data = str(data)
        if str_data in self._choice_values:
            return str_data

        self.fail("invalid_choice", input=data)
        return ""  # Never reached

    def to_representation(self, value: str) -> str:
        return value


class MultipleChoiceField(ChoiceField):
    """Multiple choice field."""

    default_error_messages = {
        **ChoiceField.default_error_messages,
        "not_a_list": 'Expected a list of items but got "{input_type}".',
        "empty": "This selection may not be empty.",
    }

    def __init__(self, *, allow_empty: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.allow_empty = allow_empty

    def to_internal_value(self, data: Any) -> list[str]:
        if not isinstance(data, (list, set, tuple)):
            self.fail("not_a_list", input_type=type(data).__name__)

        if not data and not self.allow_empty:
            self.fail("empty")

        result = []
        for item in data:
            if item not in self._choice_values:
                self.fail("invalid_choice", input=item)
            result.append(item)

        return result

    def to_representation(self, value: list[str]) -> list[str]:
        return value


# =============================================================================
# Composite Fields
# =============================================================================

class ListField(Field[list]):
    """List/array field."""

    default_error_messages = {
        **Field.default_error_messages,
        "not_a_list": 'Expected a list of items but got "{input_type}".',
        "empty": "This list may not be empty.",
        "max_length": "Ensure this list has no more than {max_length} items.",
        "min_length": "Ensure this list has at least {min_length} items.",
    }

    def __init__(
        self,
        child: Field | None = None,
        *,
        allow_empty: bool = True,
        max_length: int | None = None,
        min_length: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.child = child
        self.allow_empty = allow_empty
        self.max_length = max_length
        self.min_length = min_length

    def to_internal_value(self, data: Any) -> list:
        if not isinstance(data, (list, tuple)):
            self.fail("not_a_list", input_type=type(data).__name__)

        if not data and not self.allow_empty:
            self.fail("empty")

        if self.max_length is not None and len(data) > self.max_length:
            self.fail("max_length", max_length=self.max_length)

        if self.min_length is not None and len(data) < self.min_length:
            self.fail("min_length", min_length=self.min_length)

        if self.child is None:
            return list(data)

        return [self.child.run_validation(item) for item in data]

    def to_representation(self, value: list) -> list:
        if self.child is None:
            return value
        return [self.child.to_representation(item) for item in value]


class DictField(Field[dict]):
    """Dictionary/object field."""

    default_error_messages = {
        **Field.default_error_messages,
        "not_a_dict": 'Expected a dictionary but got "{input_type}".',
    }

    def __init__(
        self,
        child: Field | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.child = child

    def to_internal_value(self, data: Any) -> dict:
        if not isinstance(data, dict):
            self.fail("not_a_dict", input_type=type(data).__name__)

        if self.child is None:
            return dict(data)

        return {key: self.child.run_validation(value) for key, value in data.items()}

    def to_representation(self, value: dict) -> dict:
        if self.child is None:
            return value
        return {key: self.child.to_representation(v) for key, v in value.items()}


class JSONField(Field[Any]):
    """JSON field that accepts any valid JSON."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Value must be valid JSON.",
    }

    def __init__(
        self,
        *,
        binary: bool = False,
        encoder: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.binary = binary
        self.encoder = encoder

    def to_internal_value(self, data: Any) -> Any:
        import json

        if self.binary and isinstance(data, bytes):
            try:
                data = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self.fail("invalid")

        return data

    def to_representation(self, value: Any) -> Any:
        return value


# =============================================================================
# Special Fields
# =============================================================================

class HiddenField(Field):
    """Hidden field with a fixed value (not in input, always in output)."""

    def __init__(self, default: Any, **kwargs: Any) -> None:
        kwargs["write_only"] = True
        super().__init__(default=default, **kwargs)

    def to_internal_value(self, data: Any) -> Any:
        return self.default() if callable(self.default) else self.default


class ReadOnlyField(Field):
    """Read-only field that outputs a value but doesn't accept input."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> Any:
        return data


class SerializerMethodField(Field):
    """Field that calls a method on the parent serializer."""

    def __init__(self, method_name: str | None = None, **kwargs: Any) -> None:
        kwargs["read_only"] = True
        super().__init__(**kwargs)
        self.method_name = method_name

    def bind(self, field_name: str, parent: Any) -> None:
        super().bind(field_name, parent)
        if self.method_name is None:
            self.method_name = f"get_{field_name}"

    def to_representation(self, value: Any) -> Any:
        if self.parent is None:
            return None
        method = getattr(self.parent, self.method_name, None)
        if method is None:
            raise AttributeError(f"Method '{self.method_name}' not found on {self.parent.__class__.__name__}")
        return method(value)


class ConstantField(Field):
    """Field that always returns a constant value."""

    def __init__(self, value: Any, **kwargs: Any) -> None:
        kwargs["read_only"] = True
        super().__init__(**kwargs)
        self.value = value

    def to_representation(self, value: Any) -> Any:
        return self.value


# =============================================================================
# File Fields (placeholders - actual implementation in uploads.py)
# =============================================================================

class FileField(Field):
    """File upload field."""

    default_error_messages = {
        **Field.default_error_messages,
        "invalid": "Not a valid file.",
        "max_length": "Ensure the filename has no more than {max_length} characters.",
    }

    def __init__(
        self,
        *,
        max_length: int | None = None,
        allow_empty_file: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.max_length = max_length
        self.allow_empty_file = allow_empty_file

    def to_internal_value(self, data: Any) -> Any:
        # Actual file handling in uploads.py
        return data

    def to_representation(self, value: Any) -> str | None:
        if not value:
            return None
        if hasattr(value, "url"):
            return value.url
        return str(value)


class ImageField(FileField):
    """Image file upload field."""

    default_error_messages = {
        **FileField.default_error_messages,
        "invalid_image": "Upload a valid image.",
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Boolean
    "BooleanField",
    # String
    "CharField",
    # Choice
    "ChoiceField",
    "ConstantField",
    "DateField",
    # Date/Time
    "DateTimeField",
    "DecimalField",
    "DictField",
    "DurationField",
    "EmailField",
    "Empty",
    # Base
    "Field",
    # Files
    "FileField",
    "FloatField",
    # Special
    "HiddenField",
    "IPAddressField",
    "ImageField",
    # Numeric
    "IntegerField",
    "JSONField",
    # Composite
    "ListField",
    "MultipleChoiceField",
    "NullBooleanField",
    "ReadOnlyField",
    "RegexField",
    "SerializerMethodField",
    "SlugField",
    "TextField",
    "TimeField",
    "URLField",
    "UUIDField",
    "empty",
]
