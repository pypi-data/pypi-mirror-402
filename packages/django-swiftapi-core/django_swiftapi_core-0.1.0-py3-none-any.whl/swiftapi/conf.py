"""
SwiftAPI Configuration System.

Provides a centralized configuration system that reads from Django settings
under the SWIFTAPI namespace with sensible defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SwiftAPISettings:
    """
    Configuration container for SwiftAPI settings.

    All settings are read from Django's settings.py under the SWIFTAPI key.

    Example Django settings.py:
        SWIFTAPI = {
            'DEFAULT_PAGINATION_CLASS': 'swiftapi.pagination.LimitOffsetPagination',
            'PAGE_SIZE': 25,
            'DEFAULT_PERMISSION_CLASSES': ['swiftapi.permissions.IsAuthenticated'],
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'swiftapi.authentication.SessionAuthentication',
                'swiftapi.authentication.TokenAuthentication',
            ],
        }
    """

    # Pagination
    DEFAULT_PAGINATION_CLASS: str | None = "swiftapi.pagination.LimitOffsetPagination"
    PAGE_SIZE: int = 25
    MAX_PAGE_SIZE: int = 100

    # Permissions
    DEFAULT_PERMISSION_CLASSES: list[str] = field(
        default_factory=lambda: ["swiftapi.permissions.AllowAny"]
    )

    # Authentication
    DEFAULT_AUTHENTICATION_CLASSES: list[str] = field(
        default_factory=lambda: ["swiftapi.authentication.SessionAuthentication"]
    )
    UNAUTHENTICATED_USER: str | None = "django.contrib.auth.models.AnonymousUser"

    # Multi-tenancy
    TENANT_RESOLVER: str | None = None
    TENANT_HEADER: str = "X-Tenant-ID"
    TENANT_MODEL: str | None = None
    TENANT_FIELD: str = "tenant"

    # Throttling
    DEFAULT_THROTTLE_CLASSES: list[str] = field(default_factory=list)
    DEFAULT_THROTTLE_RATES: dict[str, str] = field(default_factory=dict)
    THROTTLE_BACKEND: str = "swiftapi.throttling.InMemoryThrottleBackend"

    # Response handling
    DEFAULT_RENDERER_CLASSES: list[str] = field(
        default_factory=lambda: ["swiftapi.renderers.JSONRenderer"]
    )
    DEFAULT_PARSER_CLASSES: list[str] = field(
        default_factory=lambda: ["swiftapi.parsers.JSONParser"]
    )

    # Error handling
    EXCEPTION_HANDLER: str = "swiftapi.exceptions.default_exception_handler"
    NON_FIELD_ERRORS_KEY: str = "non_field_errors"

    # Security
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = field(default_factory=list)
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB

    # Caching
    DEFAULT_CACHE_BACKEND: str = "default"
    DEFAULT_CACHE_TTL: int = 300  # 5 minutes

    # Observability
    ENABLE_REQUEST_LOGGING: bool = True
    LOG_REQUEST_BODY: bool = False
    LOG_RESPONSE_BODY: bool = False
    REQUEST_ID_HEADER: str = "X-Request-ID"
    GENERATE_REQUEST_ID: bool = True

    # OpenAPI
    SCHEMA_PATH_PREFIX: str = "/api"
    SCHEMA_TITLE: str = "API"
    SCHEMA_DESCRIPTION: str = ""
    SCHEMA_VERSION: str = "1.0.0"

    # Versioning
    DEFAULT_VERSION: str | None = None
    ALLOWED_VERSIONS: list[str] = field(default_factory=list)
    VERSION_PARAM: str = "version"

    # Async settings
    SYNC_TO_ASYNC_THREAD_SENSITIVE: bool = True

    # Content negotiation
    URL_FORMAT_OVERRIDE: str | None = "format"
    FORMAT_SUFFIX_PATH_PARAM: str = "format"

    # CORS
    CORS_ALLOWED_ORIGINS: list[str] = field(default_factory=list)
    CORS_ALLOW_ALL_ORIGINS: bool = False
    CORS_ALLOWED_METHODS: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    CORS_ALLOWED_HEADERS: list[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 86400

    # Background Tasks
    TASK_BACKEND: str | None = None
    CELERY_APP: str | None = None

    # Rate Limiting
    GLOBAL_RATE_LIMIT: str | None = None


class LazySettings:
    """
    Lazy settings loader that reads from Django settings on first access.

    This allows the settings to be imported before Django is configured.
    """

    _settings: SwiftAPISettings | None = None
    _configured: bool = False

    def __getattr__(self, name: str) -> Any:
        if not self._configured:
            self._configure()
        if self._settings is None:
            raise RuntimeError("SwiftAPI settings not configured")
        return getattr(self._settings, name)

    def _configure(self) -> None:
        """Load settings from Django configuration."""
        from django.conf import settings as django_settings

        user_settings = getattr(django_settings, "SWIFTAPI", {})
        defaults = SwiftAPISettings()

        # Apply user overrides
        settings_dict = {}
        for key in SwiftAPISettings.__dataclass_fields__:
            if key in user_settings:
                settings_dict[key] = user_settings[key]
            else:
                settings_dict[key] = getattr(defaults, key)

        self._settings = SwiftAPISettings(**settings_dict)
        self._configured = True

        # Validate settings
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        if self._settings is None:
            return

        if self._settings.PAGE_SIZE <= 0:
            raise ValueError("SWIFTAPI['PAGE_SIZE'] must be a positive integer")

        if self._settings.MAX_PAGE_SIZE < self._settings.PAGE_SIZE:
            raise ValueError(
                "SWIFTAPI['MAX_PAGE_SIZE'] must be >= SWIFTAPI['PAGE_SIZE']"
            )

        if self._settings.MAX_REQUEST_SIZE <= 0:
            raise ValueError("SWIFTAPI['MAX_REQUEST_SIZE'] must be positive")

    def reload(self) -> None:
        """Reload settings from Django configuration."""
        self._configured = False
        self._settings = None
        self._configure()

    def __repr__(self) -> str:
        if self._configured and self._settings:
            return "<SwiftAPISettings: configured>"
        return "<SwiftAPISettings: not configured>"


# Global settings instance
settings = LazySettings()


def get_setting(name: str, default: Any = None) -> Any:
    """
    Get a SwiftAPI setting value.

    Args:
        name: The setting name
        default: Default value if setting doesn't exist

    Returns:
        The setting value or default
    """
    try:
        return getattr(settings, name)
    except AttributeError:
        return default


def import_string(dotted_path: str) -> Any:
    """
    Import a class or function from a dotted path.

    Args:
        dotted_path: Full path like 'swiftapi.permissions.IsAuthenticated'

    Returns:
        The imported class or function
    """
    from importlib import import_module

    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as e:
        raise ImportError(f"'{dotted_path}' doesn't look like a module path") from e

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(
            f"Module '{module_path}' does not have a '{class_name}' attribute"
        ) from e


def import_from_string(value: str | type, setting_name: str) -> Any:
    """
    Import from string or return as-is if already a class/function.

    Args:
        value: String path or class/function
        setting_name: Name of the setting (for error messages)

    Returns:
        The imported class/function or the value as-is
    """
    if isinstance(value, str):
        try:
            return import_string(value)
        except ImportError as e:
            raise ImportError(
                f"Could not import '{value}' for SWIFTAPI setting '{setting_name}'. "
                f"Error: {e}"
            ) from e
    return value
