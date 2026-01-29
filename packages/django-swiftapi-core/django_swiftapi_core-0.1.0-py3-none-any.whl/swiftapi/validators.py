"""
SwiftAPI Validators.

Database-level validators for uniqueness and other constraints - similar to DRF's validators.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from swiftapi.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.models import QuerySet


class UniqueValidator:
    """
    Validator that checks for unique values in the database.

    Example:
        class UserSchema(Schema):
            email = CharField(validators=[UniqueValidator(queryset=User.objects.all())])
    """

    message = "This field must be unique."

    def __init__(
        self,
        queryset: QuerySet,
        message: str | None = None,
        lookup: str = "exact",
    ) -> None:
        self.queryset = queryset
        self.message = message or self.message
        self.lookup = lookup
        self.field_name: str | None = None
        self.instance: Any = None

    def set_context(self, field_name: str, instance: Any = None) -> None:
        """Set context for the validator."""
        self.field_name = field_name
        self.instance = instance

    def __call__(self, value: Any) -> None:
        """Run validation."""
        queryset = self.queryset.all()

        # Exclude current instance from check (for updates)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        filter_kwargs = {f"{self.field_name}__{self.lookup}": value}

        if queryset.filter(**filter_kwargs).exists():
            raise ValidationError({self.field_name: self.message})

    def __repr__(self) -> str:
        return f"UniqueValidator(queryset={self.queryset.model})"


class UniqueTogetherValidator:
    """
    Validator for unique_together constraints.

    Example:
        class OrderItemSchema(Schema):
            order_id: int
            product_id: int

            class Meta:
                validators = [
                    UniqueTogetherValidator(
                        queryset=OrderItem.objects.all(),
                        fields=["order_id", "product_id"],
                    )
                ]
    """

    message = "The fields {field_names} must make a unique set."

    def __init__(
        self,
        queryset: QuerySet,
        fields: list[str],
        message: str | None = None,
    ) -> None:
        self.queryset = queryset
        self.fields = fields
        self.message = message or self.message
        self.instance: Any = None

    def set_context(self, instance: Any = None) -> None:
        """Set context for the validator."""
        self.instance = instance

    def __call__(self, data: dict[str, Any]) -> None:
        """Run validation."""
        # Check if all required fields are present
        if not all(field in data for field in self.fields):
            return

        queryset = self.queryset.all()

        # Exclude current instance from check (for updates)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        # Build filter
        filter_kwargs = {field: data[field] for field in self.fields}

        if queryset.filter(**filter_kwargs).exists():
            field_names = ", ".join(self.fields)
            raise ValidationError({
                "non_field_errors": self.message.format(field_names=field_names)
            })

    def __repr__(self) -> str:
        return f"UniqueTogetherValidator(fields={self.fields})"


class UniqueForDateValidator:
    """
    Validator for unique_for_date constraints.

    Example:
        class ArticleSchema(Schema):
            slug: str
            publish_date: date

            class Meta:
                validators = [
                    UniqueForDateValidator(
                        queryset=Article.objects.all(),
                        field="slug",
                        date_field="publish_date",
                    )
                ]
    """

    message = "{field} must be unique for {date_field}."

    def __init__(
        self,
        queryset: QuerySet,
        field: str,
        date_field: str,
        message: str | None = None,
    ) -> None:
        self.queryset = queryset
        self.field = field
        self.date_field = date_field
        self.message = message or self.message
        self.instance: Any = None

    def set_context(self, instance: Any = None) -> None:
        """Set context for the validator."""
        self.instance = instance

    def __call__(self, data: dict[str, Any]) -> None:
        """Run validation."""
        if self.field not in data or self.date_field not in data:
            return

        queryset = self.queryset.all()

        # Exclude current instance from check (for updates)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        date_value = data[self.date_field]

        # Build filter for same date
        filter_kwargs = {
            self.field: data[self.field],
            f"{self.date_field}__date": date_value if hasattr(date_value, "date") else date_value,
        }

        if queryset.filter(**filter_kwargs).exists():
            raise ValidationError({
                self.field: self.message.format(field=self.field, date_field=self.date_field)
            })


class UniqueForMonthValidator(UniqueForDateValidator):
    """Validator for unique_for_month constraints."""

    message = "{field} must be unique for {date_field} month."

    def __call__(self, data: dict[str, Any]) -> None:
        """Run validation."""
        if self.field not in data or self.date_field not in data:
            return

        queryset = self.queryset.all()

        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        date_value = data[self.date_field]
        if hasattr(date_value, "month"):
            month = date_value.month
            year = date_value.year
        else:
            return

        filter_kwargs = {
            self.field: data[self.field],
            f"{self.date_field}__month": month,
            f"{self.date_field}__year": year,
        }

        if queryset.filter(**filter_kwargs).exists():
            raise ValidationError({
                self.field: self.message.format(field=self.field, date_field=self.date_field)
            })


class UniqueForYearValidator(UniqueForDateValidator):
    """Validator for unique_for_year constraints."""

    message = "{field} must be unique for {date_field} year."

    def __call__(self, data: dict[str, Any]) -> None:
        """Run validation."""
        if self.field not in data or self.date_field not in data:
            return

        queryset = self.queryset.all()

        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        date_value = data[self.date_field]
        if hasattr(date_value, "year"):
            year = date_value.year
        else:
            return

        filter_kwargs = {
            self.field: data[self.field],
            f"{self.date_field}__year": year,
        }

        if queryset.filter(**filter_kwargs).exists():
            raise ValidationError({
                self.field: self.message.format(field=self.field, date_field=self.date_field)
            })


# =============================================================================
# Common Validators (functional style)
# =============================================================================

def min_length(limit: int, message: str | None = None) -> Callable:
    """Minimum length validator."""
    msg = message or f"Ensure this value has at least {limit} characters."

    def validator(value: Any) -> None:
        if len(value) < limit:
            raise ValidationError(msg)

    return validator


def max_length(limit: int, message: str | None = None) -> Callable:
    """Maximum length validator."""
    msg = message or f"Ensure this value has no more than {limit} characters."

    def validator(value: Any) -> None:
        if len(value) > limit:
            raise ValidationError(msg)

    return validator


def min_value(limit: int | float, message: str | None = None) -> Callable:
    """Minimum value validator."""
    msg = message or f"Ensure this value is greater than or equal to {limit}."

    def validator(value: Any) -> None:
        if value < limit:
            raise ValidationError(msg)

    return validator


def max_value(limit: int | float, message: str | None = None) -> Callable:
    """Maximum value validator."""
    msg = message or f"Ensure this value is less than or equal to {limit}."

    def validator(value: Any) -> None:
        if value > limit:
            raise ValidationError(msg)

    return validator


def regex_validator(pattern: str, message: str | None = None) -> Callable:
    """Regex pattern validator."""
    import re
    compiled = re.compile(pattern)
    msg = message or "This field does not match the required pattern."

    def validator(value: Any) -> None:
        if not compiled.match(str(value)):
            raise ValidationError(msg)

    return validator


def email_validator(message: str | None = None) -> Callable:
    """Email format validator."""
    return regex_validator(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        message or "Enter a valid email address.",
    )


def url_validator(message: str | None = None) -> Callable:
    """URL format validator."""
    return regex_validator(
        r"^https?://[^\s/$.?#].[^\s]*$",
        message or "Enter a valid URL.",
    )


def slug_validator(message: str | None = None) -> Callable:
    """Slug format validator."""
    return regex_validator(
        r"^[-a-zA-Z0-9_]+$",
        message or "Enter a valid slug (letters, numbers, hyphens, underscores).",
    )


class ProhibitNullCharactersValidator:
    """Validator that prohibits null characters."""

    message = "Null characters are not allowed."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message

    def __call__(self, value: Any) -> None:
        if "\x00" in str(value):
            raise ValidationError(self.message)


class ProhibitSurrogateCharactersValidator:
    """Validator that prohibits surrogate characters."""

    message = "Surrogate characters are not allowed."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message

    def __call__(self, value: Any) -> None:
        for char in str(value):
            if 0xD800 <= ord(char) <= 0xDFFF:
                raise ValidationError(self.message)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ProhibitNullCharactersValidator",
    "ProhibitSurrogateCharactersValidator",
    "UniqueForDateValidator",
    "UniqueForMonthValidator",
    "UniqueForYearValidator",
    "UniqueTogetherValidator",
    # Class validators
    "UniqueValidator",
    "email_validator",
    "max_length",
    "max_value",
    # Function validators
    "min_length",
    "min_value",
    "regex_validator",
    "slug_validator",
    "url_validator",
]
