"""
SwiftAPI Multi-Tenancy System.

Built-in tenant isolation with multiple resolution strategies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest
    pass


class BaseTenantResolver:
    """
    Base class for tenant resolution strategies.

    Tenant resolvers extract the current tenant from the request
    and are used by middleware and viewsets for tenant isolation.
    """

    def resolve(self, request: HttpRequest) -> Any | None:
        """
        Resolve the tenant from the request.

        Args:
            request: The HTTP request

        Returns:
            Tenant object or None if no tenant
        """
        raise NotImplementedError

    async def aresolve(self, request: HttpRequest) -> Any | None:
        """
        Async version of resolve.

        Default implementation calls the sync version.
        Override for async-native resolution.
        """
        return self.resolve(request)


class HeaderTenantResolver(BaseTenantResolver):
    """
    Resolve tenant from a request header.

    Uses X-Tenant-ID header by default.

    Configuration:
        SWIFTAPI = {
            "TENANT_HEADER": "X-Tenant-ID",
            "TENANT_MODEL": "myapp.Organization",
        }
    """

    header_name = "HTTP_X_TENANT_ID"

    def __init__(
        self,
        header_name: str | None = None,
        tenant_model: str | type | None = None,
    ) -> None:
        """
        Initialize resolver.

        Args:
            header_name: Custom header name (without HTTP_ prefix)
            tenant_model: Tenant model class or dotted path
        """
        if header_name:
            self.header_name = f"HTTP_{header_name.upper().replace('-', '_')}"
        self.tenant_model = tenant_model

    def resolve(self, request: HttpRequest) -> Any | None:
        """Resolve tenant from header."""
        tenant_id = request.META.get(self.header_name)

        if not tenant_id:
            return None

        return self._get_tenant(tenant_id)

    def _get_tenant(self, tenant_id: str) -> Any | None:
        """Get tenant by ID."""
        model = self._get_model()

        if model is None:
            # Return raw ID if no model configured
            return tenant_id

        try:
            return model.objects.get(pk=tenant_id)
        except (model.DoesNotExist, ValueError):
            return None

    def _get_model(self) -> type | None:
        """Get the tenant model class."""
        from swiftapi.conf import import_string, settings

        model = self.tenant_model or settings.TENANT_MODEL

        if model is None:
            return None

        if isinstance(model, str):
            return import_string(model)

        return model


class JWTTenantResolver(BaseTenantResolver):
    """
    Resolve tenant from JWT claims.

    Extracts tenant_id from the JWT payload.
    """

    claim_name = "tenant_id"

    def __init__(
        self,
        claim_name: str | None = None,
        tenant_model: str | type | None = None,
    ) -> None:
        """
        Initialize resolver.

        Args:
            claim_name: JWT claim name for tenant ID
            tenant_model: Tenant model class or dotted path
        """
        if claim_name:
            self.claim_name = claim_name
        self.tenant_model = tenant_model

    def resolve(self, request: HttpRequest) -> Any | None:
        """Resolve tenant from JWT."""
        # Get auth payload from request (set by JWTAuthentication)
        auth = getattr(request, "auth", None)

        if not isinstance(auth, dict):
            return None

        tenant_id = auth.get(self.claim_name)

        if tenant_id is None:
            return None

        return self._get_tenant(tenant_id)

    def _get_tenant(self, tenant_id: Any) -> Any | None:
        """Get tenant by ID."""
        from swiftapi.conf import import_string, settings

        model = self.tenant_model or settings.TENANT_MODEL

        if model is None:
            return tenant_id

        if isinstance(model, str):
            model = import_string(model)

        try:
            return model.objects.get(pk=tenant_id)
        except (model.DoesNotExist, ValueError):
            return None


class SubdomainTenantResolver(BaseTenantResolver):
    """
    Resolve tenant from request subdomain.

    Extracts tenant slug from subdomain:
    - https://acme.example.com/ -> tenant slug "acme"
    """

    def __init__(
        self,
        base_domain: str | None = None,
        tenant_model: str | type | None = None,
        lookup_field: str = "slug",
    ) -> None:
        """
        Initialize resolver.

        Args:
            base_domain: Base domain (e.g., "example.com")
            tenant_model: Tenant model class or dotted path
            lookup_field: Field to use for tenant lookup
        """
        self.base_domain = base_domain
        self.tenant_model = tenant_model
        self.lookup_field = lookup_field

    def resolve(self, request: HttpRequest) -> Any | None:
        """Resolve tenant from subdomain."""
        host = request.get_host().split(":")[0]  # Remove port

        if not self.base_domain:
            # Auto-detect base domain from settings
            from django.conf import settings as django_settings
            allowed = getattr(django_settings, "ALLOWED_HOSTS", [])
            # Find a domain that's a suffix of the host
            for domain in allowed:
                if domain.startswith("."):
                    self.base_domain = domain[1:]
                    break

        if not self.base_domain:
            return None

        # Extract subdomain
        if not host.endswith(self.base_domain):
            return None

        subdomain = host[: -len(self.base_domain)].rstrip(".")

        if not subdomain or subdomain == "www":
            return None

        return self._get_tenant(subdomain)

    def _get_tenant(self, slug: str) -> Any | None:
        """Get tenant by slug."""
        from swiftapi.conf import import_string, settings

        model = self.tenant_model or settings.TENANT_MODEL

        if model is None:
            return slug

        if isinstance(model, str):
            model = import_string(model)

        try:
            return model.objects.get(**{self.lookup_field: slug})
        except (model.DoesNotExist, ValueError):
            return None


class PathTenantResolver(BaseTenantResolver):
    """
    Resolve tenant from URL path.

    Extracts tenant from URL path:
    - /api/tenant/acme/users/ -> tenant slug "acme"
    """

    def __init__(
        self,
        path_prefix: str = "tenant",
        tenant_model: str | type | None = None,
        lookup_field: str = "slug",
    ) -> None:
        """
        Initialize resolver.

        Args:
            path_prefix: URL path prefix before tenant slug
            tenant_model: Tenant model class or dotted path
            lookup_field: Field to use for tenant lookup
        """
        self.path_prefix = path_prefix
        self.tenant_model = tenant_model
        self.lookup_field = lookup_field

    def resolve(self, request: HttpRequest) -> Any | None:
        """Resolve tenant from URL path."""
        import re

        path = request.path

        # Match /prefix/slug/ or /prefix/slug/rest/of/path
        pattern = rf"/{self.path_prefix}/([^/]+)"
        match = re.match(pattern, path)

        if not match:
            return None

        slug = match.group(1)
        return self._get_tenant(slug)

    def _get_tenant(self, slug: str) -> Any | None:
        """Get tenant by slug."""
        from swiftapi.conf import import_string, settings

        model = self.tenant_model or settings.TENANT_MODEL

        if model is None:
            return slug

        if isinstance(model, str):
            model = import_string(model)

        try:
            return model.objects.get(**{self.lookup_field: slug})
        except (model.DoesNotExist, ValueError):
            return None


class UserTenantResolver(BaseTenantResolver):
    """
    Resolve tenant from authenticated user.

    Uses user.tenant or user.organization field.
    """

    def __init__(self, tenant_field: str = "tenant") -> None:
        """
        Initialize resolver.

        Args:
            tenant_field: Field name on user model for tenant
        """
        self.tenant_field = tenant_field

    def resolve(self, request: HttpRequest) -> Any | None:
        """Resolve tenant from user."""
        user = getattr(request, "user", None)

        if user is None or not user.is_authenticated:
            return None

        return getattr(user, self.tenant_field, None)


class TenantMiddleware:
    """
    Django middleware for tenant resolution.

    Resolves the current tenant and sets it on the request.

    Add to MIDDLEWARE:
        MIDDLEWARE = [
            # ...
            "swiftapi.tenancy.TenantMiddleware",
            # ...
        ]

    Configure resolver in settings:
        SWIFTAPI = {
            "TENANT_RESOLVER": "swiftapi.tenancy.HeaderTenantResolver",
            "TENANT_MODEL": "myapp.Organization",
        }
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        self._resolver: BaseTenantResolver | None = None

    def __call__(self, request: HttpRequest):
        """Process the request."""
        # Resolve tenant
        request.tenant = self._resolve_tenant(request)  # type: ignore

        # Call next middleware/view
        response = self.get_response(request)

        return response

    async def __acall__(self, request: HttpRequest):
        """Async request processing."""
        # Resolve tenant
        resolver = self._get_resolver()
        if resolver:
            request.tenant = await resolver.aresolve(request)  # type: ignore
        else:
            request.tenant = None  # type: ignore

        # Call next middleware/view
        response = await self.get_response(request)

        return response

    def _resolve_tenant(self, request: HttpRequest) -> Any | None:
        """Resolve tenant from request."""
        resolver = self._get_resolver()

        if resolver is None:
            return None

        return resolver.resolve(request)

    def _get_resolver(self) -> BaseTenantResolver | None:
        """Get the configured tenant resolver."""
        if self._resolver is not None:
            return self._resolver

        from swiftapi.conf import import_string, settings

        resolver_path = settings.TENANT_RESOLVER

        if resolver_path is None:
            return None

        resolver_class = import_string(resolver_path)
        self._resolver = resolver_class()

        return self._resolver


class TenantAwareManager:
    """
    Mixin for Django model managers to add tenant filtering.

    Usage:
        class Article(models.Model):
            tenant = models.ForeignKey(Organization, on_delete=models.CASCADE)
            title = models.CharField(max_length=200)

            objects = TenantAwareManager()
    """

    tenant_field = "tenant"

    def get_queryset(self):
        """Get queryset filtered by current tenant."""

        qs = super().get_queryset()  # type: ignore

        # Get current tenant from thread-local storage
        current_tenant = getattr(_tenant_context, "tenant", None)

        if current_tenant is not None:
            qs = qs.filter(**{self.tenant_field: current_tenant})

        return qs


# Thread-local storage for tenant context
from threading import local

_tenant_context = local()


def set_current_tenant(tenant: Any) -> None:
    """
    Set the current tenant for this thread/request.

    Args:
        tenant: Tenant object to set
    """
    _tenant_context.tenant = tenant


def get_current_tenant() -> Any | None:
    """
    Get the current tenant for this thread/request.

    Returns:
        Current tenant or None
    """
    return getattr(_tenant_context, "tenant", None)


def clear_current_tenant() -> None:
    """Clear the current tenant."""
    _tenant_context.tenant = None
