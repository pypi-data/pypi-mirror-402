"""
SwiftAPI - Async-First API Framework for Django.

A modern, high-performance alternative to Django REST Framework
with async-first design, lightweight schemas, and built-in multi-tenancy.
"""

__version__ = "0.1.0"
__author__ = "SwiftAPI Contributors"
__license__ = "MIT"

# Core imports for public API
# Authentication
from swiftapi.authentication import (
    APIKeyAuthentication,
    BasicAuthentication,
    BearerTokenAuthentication,
    JWTAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)

# Browsable API
from swiftapi.browsable import (
    BrowsableAPIMixin,
    BrowsableAPIRenderer,
    get_browsable_api_view,
)

# Bulk operations
from swiftapi.bulk import BulkMixin

# Caching
from swiftapi.caching import (
    ETagMixin,
    LastModifiedMixin,
    ResponseCache,
    cache_response,
)
from swiftapi.conf import settings

# Content negotiation
from swiftapi.content import (
    CSVRenderer,
    HTMLRenderer,
    JSONRenderer,
    XMLRenderer,
)
from swiftapi.crud import create_crud_viewset, create_read_only_viewset, model_to_schema

# Decorators (DRF equivalent)
from swiftapi.decorators import (
    action,
    api_view,
)
from swiftapi.decorators import (
    authentication_classes as authentication_classes_decorator,
)
from swiftapi.decorators import (
    permission_classes as permission_classes_decorator,
)
from swiftapi.decorators import (
    throttle_classes as throttle_classes_decorator,
)

# Events
from swiftapi.events import (
    CRUDEvents,
    Event,
    EventEmitterMixin,
    event_bus,
    on_event,
)

# Exceptions
from swiftapi.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)

# Fields (DRF equivalent)
from swiftapi.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    DictField,
    DurationField,
    EmailField,
    Field,
    FloatField,
    HiddenField,
    IntegerField,
    IPAddressField,
    JSONField,
    ListField,
    MultipleChoiceField,
    ReadOnlyField,
    RegexField,
    SerializerMethodField,
    SlugField,
    TextField,
    TimeField,
    URLField,
    UUIDField,
)

# Filtering
from swiftapi.filters import (
    FilterSet,
    OrderingFilter,
    QueryFilter,
    SearchFilter,
    apply_filters,
)

# Generics (DRF equivalent)
from swiftapi.generics import (
    CreateAPIView,
    CreateModelMixin,
    DestroyAPIView,
    DestroyModelMixin,
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    ListModelMixin,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
    RetrieveModelMixin,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
    UpdateModelMixin,
)

# Lifecycle hooks
from swiftapi.lifecycle import (
    LifecycleMixin,
    TransactionMixin,
    after_request,
    before_request,
    on_error,
    on_success,
)

# Metadata (DRF equivalent)
from swiftapi.metadata import (
    MinimalMetadata,
    SimpleMetadata,
    get_options_response,
)

# OpenAPI
from swiftapi.openapi import (
    OpenAPIGenerator,
    get_openapi_view,
    get_swagger_ui_view,
)

# Pagination
from swiftapi.pagination import (
    CursorPagination,
    LimitOffsetPagination,
    PageNumberPagination,
)

# Permissions
from swiftapi.permissions import (
    AllowAny,
    DenyAll,
    HasRole,
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    IsOwner,
    IsSuperUser,
    IsTenantMember,
    OperationPermission,
    and_permissions,
    or_permissions,
)

# Relations (DRF equivalent)
from swiftapi.relations import (
    HyperlinkedIdentityField,
    HyperlinkedRelatedField,
    NestedSerializer,
    PrimaryKeyRelatedField,
    SlugRelatedField,
    StringRelatedField,
)

# Responses
from swiftapi.responses import (
    CreatedResponse,
    ErrorResponse,
    NoContentResponse,
    PaginatedResponse,
    Response,
    SuccessResponse,
)

# Reverse (DRF equivalent)
from swiftapi.reverse import (
    reverse,
    reverse_lazy,
)
from swiftapi.routing import NestedRouter, Router, SimpleRouter
from swiftapi.schemas import Field as SchemaField
from swiftapi.schemas import Schema

# Status codes (DRF equivalent)
from swiftapi.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

# Background Tasks
from swiftapi.tasks import (
    after_response,
    background_task,
    get_task_backend,
    get_task_status_view,
)

# Multi-tenancy
from swiftapi.tenancy import (
    HeaderTenantResolver,
    JWTTenantResolver,
    PathTenantResolver,
    SubdomainTenantResolver,
    TenantMiddleware,
    UserTenantResolver,
    get_current_tenant,
    set_current_tenant,
)

# Testing
from swiftapi.testing import (
    AsyncAPIClient,
    AsyncTestCase,
    SchemaFactory,
    assert_contains,
    assert_data_contains,
    assert_json_equal,
    assert_status,
)

# Throttling
from swiftapi.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    SimpleRateThrottle,
    UserRateThrottle,
)

# Uploads
from swiftapi.uploads import (
    FileField,
    FileHandler,
    ImageField,
    MultipleFileField,
)

# Validators (DRF equivalent)
from swiftapi.validators import (
    UniqueForDateValidator,
    UniqueForMonthValidator,
    UniqueForYearValidator,
    UniqueTogetherValidator,
    UniqueValidator,
    max_length,
    max_value,
    min_length,
    min_value,
)

# Versioning
from swiftapi.versioning import (
    HeaderVersioning,
    QueryParameterVersioning,
    URLPathVersioning,
    VersionedRouter,
)
from swiftapi.viewsets import GenericViewSet, ModelViewSet, ReadOnlyViewSet, ViewSet

__all__ = [
    # Exceptions
    "APIException",
    "APIKeyAuthentication",
    # Permissions
    "AllowAny",
    "AnonRateThrottle",
    # Testing
    "AsyncAPIClient",
    "AsyncTestCase",
    "AuthenticationFailed",
    "BasicAuthentication",
    "BearerTokenAuthentication",
    "BrowsableAPIMixin",
    # Browsable API
    "BrowsableAPIRenderer",
    # Bulk
    "BulkMixin",
    "CRUDEvents",
    "CSVRenderer",
    "CreatedResponse",
    "CursorPagination",
    "DenyAll",
    "ETagMixin",
    "ErrorResponse",
    "Event",
    "EventEmitterMixin",
    "Field",
    # Uploads
    "FileField",
    "FileHandler",
    "FilterSet",
    "GenericViewSet",
    "HTMLRenderer",
    "HasRole",
    "HeaderTenantResolver",
    "HeaderVersioning",
    "ImageField",
    "IsAdminUser",
    "IsAuthenticated",
    "IsAuthenticatedOrReadOnly",
    "IsOwner",
    "IsSuperUser",
    "IsTenantMember",
    # Content
    "JSONRenderer",
    "JWTAuthentication",
    "JWTTenantResolver",
    "LastModifiedMixin",
    # Lifecycle
    "LifecycleMixin",
    # Pagination
    "LimitOffsetPagination",
    "MethodNotAllowed",
    "ModelViewSet",
    "MultipleFileField",
    "NestedRouter",
    "NoContentResponse",
    "NotAcceptable",
    "NotAuthenticated",
    "NotFound",
    # OpenAPI
    "OpenAPIGenerator",
    "OperationPermission",
    "OrderingFilter",
    "PageNumberPagination",
    "PaginatedResponse",
    "PathTenantResolver",
    "PermissionDenied",
    # Filtering
    "QueryFilter",
    "QueryParameterVersioning",
    "ReadOnlyViewSet",
    # Responses
    "Response",
    # Caching
    "ResponseCache",
    "Router",
    # Core
    "Schema",
    "SchemaFactory",
    "ScopedRateThrottle",
    "SearchFilter",
    # Authentication
    "SessionAuthentication",
    # Throttling
    "SimpleRateThrottle",
    "SimpleRouter",
    "SubdomainTenantResolver",
    "SuccessResponse",
    # Tenancy
    "TenantMiddleware",
    "Throttled",
    "TokenAuthentication",
    "TransactionMixin",
    # Versioning
    "URLPathVersioning",
    "UserRateThrottle",
    "UserTenantResolver",
    "ValidationError",
    "VersionedRouter",
    "ViewSet",
    "XMLRenderer",
    "__author__",
    "__license__",
    # Version info
    "__version__",
    "action",
    "after_request",
    "after_response",
    "and_permissions",
    "apply_filters",
    "assert_contains",
    "assert_data_contains",
    "assert_json_equal",
    "assert_status",
    # Tasks
    "background_task",
    "before_request",
    "cache_response",
    # CRUD
    "create_crud_viewset",
    "create_read_only_viewset",
    # Events
    "event_bus",
    "get_browsable_api_view",
    "get_current_tenant",
    "get_openapi_view",
    "get_swagger_ui_view",
    "get_task_backend",
    "get_task_status_view",
    "model_to_schema",
    "on_error",
    "on_event",
    "on_success",
    "or_permissions",
    "set_current_tenant",
    # Settings
    "settings",
]
