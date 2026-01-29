"""
SwiftAPI Relational Fields.

Fields for handling relationships between models - similar to DRF's relations.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from swiftapi.exceptions import ValidationError
from swiftapi.fields import Field

if TYPE_CHECKING:
    from django.db.models import QuerySet

T = TypeVar("T")


class RelatedField(Field[T], Generic[T]):
    """
    Base class for relational fields.

    Relational fields handle ForeignKey, ManyToMany, and other relationships.
    """

    queryset: QuerySet | None = None

    default_error_messages = {
        **Field.default_error_messages,
        "does_not_exist": "Object with {pk_field}={value} does not exist.",
        "incorrect_type": "Incorrect type. Expected pk value, received {data_type}.",
    }

    def __init__(
        self,
        queryset: QuerySet | None = None,
        *,
        many: bool = False,
        pk_field: str = "pk",
        **kwargs: Any,
    ) -> None:
        self.queryset = queryset
        self.many = many
        self.pk_field = pk_field
        super().__init__(**kwargs)

    def get_queryset(self) -> QuerySet:
        """Get the queryset for lookups."""
        if self.queryset is None:
            raise ValueError("RelatedField requires a queryset.")
        return self.queryset.all()

    def to_internal_value(self, data: Any) -> T:
        """Convert input to model instance(s)."""
        raise NotImplementedError()

    def to_representation(self, value: T) -> Any:
        """Convert model instance(s) to output."""
        raise NotImplementedError()


class PrimaryKeyRelatedField(RelatedField):
    """
    Field for ForeignKey relationships using primary key.

    Example:
        author = PrimaryKeyRelatedField(queryset=User.objects.all())
        tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    """

    default_error_messages = {
        **RelatedField.default_error_messages,
        "required": "This field is required.",
        "does_not_exist": 'Invalid pk "{pk_value}" - object does not exist.',
        "incorrect_type": "Incorrect type. Expected pk value, received {data_type}.",
    }

    def __init__(
        self,
        queryset: QuerySet | None = None,
        *,
        pk_field: str = "pk",
        **kwargs: Any,
    ) -> None:
        self.pk_field = pk_field
        super().__init__(queryset=queryset, **kwargs)

    def to_internal_value(self, data: Any) -> Any:
        if self.many:
            if not isinstance(data, (list, tuple)):
                self.fail("incorrect_type", data_type=type(data).__name__)
            return [self._get_object(pk) for pk in data]
        return self._get_object(data)

    def _get_object(self, pk: Any) -> Any:
        """Get single object by primary key."""
        queryset = self.get_queryset()
        try:
            return queryset.get(**{self.pk_field: pk})
        except queryset.model.DoesNotExist:
            self.fail("does_not_exist", pk_value=pk)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(pk).__name__)

    def to_representation(self, value: Any) -> Any:
        if self.many:
            return [getattr(obj, self.pk_field) for obj in value.all()]
        if value is None:
            return None
        return getattr(value, self.pk_field)


class SlugRelatedField(RelatedField):
    """
    Field for ForeignKey relationships using a slug field.

    Example:
        author = SlugRelatedField(queryset=User.objects.all(), slug_field="username")
    """

    default_error_messages = {
        **RelatedField.default_error_messages,
        "does_not_exist": 'Object with {slug_name}="{value}" does not exist.',
        "invalid": "Invalid value.",
    }

    def __init__(
        self,
        slug_field: str,
        queryset: QuerySet | None = None,
        **kwargs: Any,
    ) -> None:
        self.slug_field = slug_field
        super().__init__(queryset=queryset, **kwargs)

    def to_internal_value(self, data: Any) -> Any:
        if self.many:
            if not isinstance(data, (list, tuple)):
                self.fail("incorrect_type", data_type=type(data).__name__)
            return [self._get_object(slug) for slug in data]
        return self._get_object(data)

    def _get_object(self, slug: Any) -> Any:
        """Get single object by slug."""
        queryset = self.get_queryset()
        try:
            return queryset.get(**{self.slug_field: slug})
        except queryset.model.DoesNotExist:
            self.fail("does_not_exist", slug_name=self.slug_field, value=slug)
        except (TypeError, ValueError):
            self.fail("invalid")

    def to_representation(self, value: Any) -> Any:
        if self.many:
            return [getattr(obj, self.slug_field) for obj in value.all()]
        if value is None:
            return None
        return getattr(value, self.slug_field)


class HyperlinkedRelatedField(RelatedField):
    """
    Field for ForeignKey relationships using hyperlinks (HATEOAS).

    Example:
        author = HyperlinkedRelatedField(
            view_name="user-detail",
            queryset=User.objects.all(),
        )
    """

    lookup_field = "pk"

    default_error_messages = {
        **RelatedField.default_error_messages,
        "no_match": "Invalid hyperlink - No URL match.",
        "incorrect_match": "Invalid hyperlink - Incorrect URL match.",
        "does_not_exist": "Invalid hyperlink - Object does not exist.",
        "incorrect_type": "Incorrect type. Expected URL string, received {data_type}.",
    }

    def __init__(
        self,
        view_name: str,
        queryset: QuerySet | None = None,
        *,
        lookup_field: str = "pk",
        lookup_url_kwarg: str | None = None,
        format: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.view_name = view_name
        self.lookup_field = lookup_field
        self.lookup_url_kwarg = lookup_url_kwarg or lookup_field
        self.format = format
        super().__init__(queryset=queryset, **kwargs)

    def to_internal_value(self, data: Any) -> Any:
        if not isinstance(data, str):
            self.fail("incorrect_type", data_type=type(data).__name__)

        # Parse URL to extract lookup value
        from django.urls import resolve

        try:
            match = resolve(data)
        except Exception:
            self.fail("no_match")

        lookup_value = match.kwargs.get(self.lookup_url_kwarg)
        if lookup_value is None:
            self.fail("incorrect_match")

        queryset = self.get_queryset()
        try:
            return queryset.get(**{self.lookup_field: lookup_value})
        except queryset.model.DoesNotExist:
            self.fail("does_not_exist")

    def to_representation(self, value: Any) -> str | None:
        if value is None:
            return None

        from django.urls import reverse

        lookup_value = getattr(value, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}

        return reverse(self.view_name, kwargs=kwargs)


class HyperlinkedIdentityField(HyperlinkedRelatedField):
    """
    Field for self-links (HATEOAS identity).

    Example:
        url = HyperlinkedIdentityField(view_name="user-detail")
    """

    def __init__(self, view_name: str, **kwargs: Any) -> None:
        kwargs["read_only"] = True
        kwargs["source"] = "*"
        super().__init__(view_name, **kwargs)

    def to_internal_value(self, data: Any) -> Any:
        raise ValidationError("This field is read-only.")


class StringRelatedField(RelatedField):
    """
    Field that represents related object using its string representation.

    Example:
        author = StringRelatedField()  # Uses str(author)
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value: Any) -> str:
        if self.many:
            return [str(obj) for obj in value.all()]
        return str(value)


class NestedSerializer(RelatedField):
    """
    Field that uses a nested serializer for related objects.

    Example:
        author = NestedSerializer(UserSchema)
        tags = NestedSerializer(TagSchema, many=True)
    """

    def __init__(
        self,
        serializer_class: type,
        *,
        many: bool = False,
        read_only: bool = False,
        **kwargs: Any,
    ) -> None:
        self.serializer_class = serializer_class
        kwargs["many"] = many
        kwargs["read_only"] = read_only
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> Any:
        if self.many:
            return [self.serializer_class().validate(item) for item in data]
        return self.serializer_class().validate(data)

    def to_representation(self, value: Any) -> Any:
        if self.many:
            return [self.serializer_class().serialize(obj) for obj in value.all()]
        return self.serializer_class().serialize(value)


class ManyRelatedField(Field):
    """
    Wrapper for handling many=True on related fields.
    """

    default_error_messages = {
        **Field.default_error_messages,
        "not_a_list": 'Expected a list of items but got "{input_type}".',
    }

    def __init__(
        self,
        child_relation: RelatedField,
        **kwargs: Any,
    ) -> None:
        self.child_relation = child_relation
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> list:
        if not isinstance(data, (list, tuple)):
            self.fail("not_a_list", input_type=type(data).__name__)
        return [self.child_relation.to_internal_value(item) for item in data]

    def to_representation(self, value: Any) -> list:
        return [self.child_relation.to_representation(obj) for obj in value.all()]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "HyperlinkedIdentityField",
    "HyperlinkedRelatedField",
    "ManyRelatedField",
    "NestedSerializer",
    "PrimaryKeyRelatedField",
    "RelatedField",
    "SlugRelatedField",
    "StringRelatedField",
]
