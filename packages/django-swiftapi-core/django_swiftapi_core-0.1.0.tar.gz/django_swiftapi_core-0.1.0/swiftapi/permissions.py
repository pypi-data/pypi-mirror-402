"""
SwiftAPI Permission System.

Declarative permissions for authorization with async support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.http import HttpRequest

    from swiftapi.viewsets import ViewSet


class BasePermission:
    """
    Base class for all permissions.

    Permissions are evaluated before executing ViewSet handlers.
    Override has_permission() and/or has_object_permission() to
    implement custom authorization logic.

    All permission methods support async execution.
    """

    message: str = "Permission denied."

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        """
        Check if request has permission to access the view.

        Called before the handler executes, for all actions.

        Args:
            request: The current HTTP request
            view: The ViewSet instance

        Returns:
            True if permission is granted, False otherwise
        """
        return True

    async def has_object_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
        obj: Any,
    ) -> bool:
        """
        Check if request has permission to access a specific object.

        Called after get_object(), for detail actions.

        Args:
            request: The current HTTP request
            view: The ViewSet instance
            obj: The object being accessed

        Returns:
            True if permission is granted, False otherwise
        """
        return True


class AllowAny(BasePermission):
    """
    Allow any access.

    This permission class will permit unrestricted access,
    regardless of whether the request is authenticated or not.
    """

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        return True


class IsAuthenticated(BasePermission):
    """
    Only allow authenticated users.

    Denies access to unauthenticated users (AnonymousUser).
    """

    message = "Authentication required."

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        return (
            hasattr(request, "user")
            and request.user is not None
            and request.user.is_authenticated
        )


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allow read-only access to unauthenticated users.

    Authenticated users get full access, while anonymous users
    can only perform safe methods (GET, HEAD, OPTIONS).
    """

    message = "Authentication required for this action."
    SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        if request.method in self.SAFE_METHODS:
            return True

        return (
            hasattr(request, "user")
            and request.user is not None
            and request.user.is_authenticated
        )


class IsAdminUser(BasePermission):
    """
    Only allow admin/staff users.

    Requires user.is_staff to be True.
    """

    message = "Admin access required."

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        return (
            hasattr(request, "user")
            and request.user is not None
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsSuperUser(BasePermission):
    """
    Only allow superusers.

    Requires user.is_superuser to be True.
    """

    message = "Superuser access required."

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        return (
            hasattr(request, "user")
            and request.user is not None
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsOwner(BasePermission):
    """
    Only allow owners of an object.

    Checks if obj.user or obj.owner matches request.user.
    """

    message = "You do not own this resource."
    owner_field = "user"

    async def has_object_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
        obj: Any,
    ) -> bool:
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return False

        # Try common owner field names
        owner = getattr(obj, self.owner_field, None)
        if owner is None:
            owner = getattr(obj, "owner", None)
        if owner is None:
            owner = getattr(obj, "created_by", None)

        if owner is None:
            return False

        # Handle both direct user and user ID comparison
        if hasattr(owner, "pk"):
            return owner.pk == request.user.pk
        return owner == request.user.pk


class IsTenantMember(BasePermission):
    """
    Only allow users who belong to the current tenant.

    Requires request.tenant and checks if user is a member.
    """

    message = "You are not a member of this tenant."

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return False

        if not hasattr(request, "tenant") or request.tenant is None:
            return True  # No tenant context, allow

        tenant = request.tenant
        user = request.user

        # Check if user has tenants relationship
        if hasattr(user, "tenants"):
            # ManyToMany relationship
            return await self._user_in_tenants(user, tenant)

        # Check if user has tenant field
        if hasattr(user, "tenant"):
            user_tenant = getattr(user, "tenant", None)
            if hasattr(user_tenant, "pk"):
                return user_tenant.pk == tenant.pk
            return user_tenant == tenant

        return False

    async def _user_in_tenants(self, user: Any, tenant: Any) -> bool:
        """Check if user belongs to tenant via M2M."""
        try:
            # Use async filter
            exists = await user.tenants.filter(pk=tenant.pk).aexists()
            return exists
        except Exception:
            return False


class HasRole(BasePermission):
    """
    Require user to have a specific role.

    Usage:
        permission_classes = [HasRole("admin")]
    """

    def __init__(self, *roles: str):
        """
        Initialize with required roles.

        Args:
            *roles: Role names (user must have at least one)
        """
        self.roles = roles
        self.message = f"Required role: {', '.join(roles)}"

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return False

        user = request.user

        # Check user.role field
        if hasattr(user, "role"):
            return user.role in self.roles

        # Check user.roles relationship
        if hasattr(user, "roles"):
            try:
                user_roles = [r.name for r in await user.roles.aall()]
                return any(r in self.roles for r in user_roles)
            except Exception:
                return False

        # Check user.groups (Django groups)
        if hasattr(user, "groups"):
            try:
                group_names = [g.name async for g in user.groups.all()]
                return any(r in self.roles for r in group_names)
            except Exception:
                return False

        return False


class DenyAll(BasePermission):
    """
    Deny all access.

    Useful for explicitly disabling an endpoint.
    """

    message = "Access denied."

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        return False


class OperationPermission(BasePermission):
    """
    Define different permissions per operation.

    Usage:
        permission_classes = [OperationPermission(
            list=[AllowAny],
            create=[IsAuthenticated],
            retrieve=[AllowAny],
            update=[IsOwner],
            destroy=[IsAdminUser],
        )]
    """

    def __init__(
        self,
        list: list[type[BasePermission]] | None = None,
        create: list[type[BasePermission]] | None = None,
        retrieve: list[type[BasePermission]] | None = None,
        update: list[type[BasePermission]] | None = None,
        partial_update: list[type[BasePermission]] | None = None,
        destroy: list[type[BasePermission]] | None = None,
        default: list[type[BasePermission]] | None = None,
        **custom_actions: list[type[BasePermission]],
    ):
        self.permission_map = {
            "list": list,
            "create": create,
            "retrieve": retrieve,
            "update": update,
            "partial_update": partial_update or update,
            "destroy": destroy,
        }
        self.permission_map.update(custom_actions)
        self.default = default or [AllowAny]

    async def has_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        action = getattr(view, "action", None)
        permissions = self.permission_map.get(action) or self.default

        for permission_class in permissions:
            permission = permission_class()
            if not await permission.has_permission(request, view):
                self.message = permission.message
                return False

        return True

    async def has_object_permission(
        self,
        request: HttpRequest,
        view: ViewSet,
        obj: Any,
    ) -> bool:
        action = getattr(view, "action", None)
        permissions = self.permission_map.get(action) or self.default

        for permission_class in permissions:
            permission = permission_class()
            if not await permission.has_object_permission(request, view, obj):
                self.message = permission.message
                return False

        return True


# Convenience function for combining permissions
def and_permissions(*permissions: type[BasePermission]) -> type[BasePermission]:
    """
    Combine permissions with AND logic.

    All permissions must pass.

    Usage:
        permission_classes = [and_permissions(IsAuthenticated, IsOwner)]
    """
    class CombinedPermission(BasePermission):
        async def has_permission(self, request: HttpRequest, view: ViewSet) -> bool:
            for perm_class in permissions:
                perm = perm_class()
                if not await perm.has_permission(request, view):
                    self.message = perm.message
                    return False
            return True

        async def has_object_permission(
            self, request: HttpRequest, view: ViewSet, obj: Any
        ) -> bool:
            for perm_class in permissions:
                perm = perm_class()
                if not await perm.has_object_permission(request, view, obj):
                    self.message = perm.message
                    return False
            return True

    return CombinedPermission


def or_permissions(*permissions: type[BasePermission]) -> type[BasePermission]:
    """
    Combine permissions with OR logic.

    At least one permission must pass.

    Usage:
        permission_classes = [or_permissions(IsAdminUser, IsOwner)]
    """
    class CombinedPermission(BasePermission):
        async def has_permission(self, request: HttpRequest, view: ViewSet) -> bool:
            for perm_class in permissions:
                perm = perm_class()
                if await perm.has_permission(request, view):
                    return True
            self.message = "None of the required permissions were satisfied."
            return False

        async def has_object_permission(
            self, request: HttpRequest, view: ViewSet, obj: Any
        ) -> bool:
            for perm_class in permissions:
                perm = perm_class()
                if await perm.has_object_permission(request, view, obj):
                    return True
            self.message = "None of the required permissions were satisfied."
            return False

    return CombinedPermission
