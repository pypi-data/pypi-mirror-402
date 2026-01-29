"""
SwiftAPI Authentication System.

Multiple authentication backends with async support.
"""

from __future__ import annotations

import base64
import binascii
from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model

from swiftapi.exceptions import AuthenticationFailed

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from django.http import HttpRequest


class BaseAuthentication:
    """
    Base class for authentication backends.

    All authentication backends should inherit from this class
    and implement the authenticate() method.
    """

    def authenticate(
        self,
        request: HttpRequest,
    ) -> tuple[AbstractUser, Any] | None:
        """
        Authenticate the request.

        Args:
            request: The HTTP request

        Returns:
            Tuple of (user, auth_info) if authenticated, None otherwise

        Raises:
            AuthenticationFailed: If authentication fails
        """
        raise NotImplementedError

    def authenticate_header(self, request: HttpRequest) -> str | None:
        """
        Return the WWW-Authenticate header value.

        Args:
            request: The HTTP request

        Returns:
            Header value or None
        """
        return None


class SessionAuthentication(BaseAuthentication):
    """
    Authentication using Django's session framework.

    Uses Django's built-in session authentication.
    Good for browser-based applications.
    """

    def authenticate(
        self,
        request: HttpRequest,
    ) -> tuple[AbstractUser, None] | None:
        """Authenticate using session."""
        user = getattr(request, "user", None)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not user.is_authenticated:
            return None

        # CSRF check for session auth (if not already done by middleware)
        self._enforce_csrf(request)

        return (user, None)

    def _enforce_csrf(self, request: HttpRequest) -> None:
        """Ensure CSRF cookie is set for session authentication."""
        from django.middleware.csrf import CsrfViewMiddleware

        reason = CsrfViewMiddleware().process_view(request, None, (), {})
        if reason:
            # CSRF check failed
            raise AuthenticationFailed("CSRF validation failed.")


class TokenAuthentication(BaseAuthentication):
    """
    Token-based authentication.

    Uses a token passed in the Authorization header:
    Authorization: Token <token>

    Requires a Token model with:
    - key: CharField with the token value
    - user: ForeignKey to User
    """

    keyword = "Token"
    model = None  # Set to your Token model

    def authenticate(
        self,
        request: HttpRequest,
    ) -> tuple[AbstractUser, Any] | None:
        """Authenticate using token."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2:
            return None

        if parts[0].lower() != self.keyword.lower():
            return None

        token_key = parts[1]

        return self._authenticate_credentials(token_key)

    def _authenticate_credentials(
        self,
        key: str,
    ) -> tuple[AbstractUser, Any]:
        """Validate the token and return user."""
        model = self._get_model()

        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")

        if not token.user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        return (token.user, token)

    def _get_model(self):
        """Get the Token model."""
        if self.model is not None:
            return self.model

        # Try to import from rest_framework for compatibility
        try:
            from rest_framework.authtoken.models import Token
            return Token
        except ImportError:
            pass

        raise ValueError(
            "TokenAuthentication requires a Token model. "
            "Set TokenAuthentication.model or install djangorestframework."
        )

    def authenticate_header(self, request: HttpRequest) -> str:
        return self.keyword


class BearerTokenAuthentication(TokenAuthentication):
    """
    Bearer token authentication.

    Uses Authorization: Bearer <token> header.
    """

    keyword = "Bearer"


class BasicAuthentication(BaseAuthentication):
    """
    HTTP Basic authentication.

    Uses Authorization: Basic <base64(username:password)> header.
    """

    def authenticate(
        self,
        request: HttpRequest,
    ) -> tuple[AbstractUser, None] | None:
        """Authenticate using basic auth."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "basic":
            return None

        try:
            credentials = base64.b64decode(parts[1]).decode("utf-8")
            username, password = credentials.split(":", 1)
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise AuthenticationFailed("Invalid basic auth credentials.")

        return self._authenticate_credentials(username, password, request)

    def _authenticate_credentials(
        self,
        username: str,
        password: str,
        request: HttpRequest,
    ) -> tuple[AbstractUser, None]:
        """Validate username and password."""
        from django.contrib.auth import authenticate

        user = authenticate(request=request, username=username, password=password)

        if user is None:
            raise AuthenticationFailed("Invalid username or password.")

        if not user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        return (user, None)

    def authenticate_header(self, request: HttpRequest) -> str:
        return 'Basic realm="api"'


class JWTAuthentication(BaseAuthentication):
    """
    JWT (JSON Web Token) authentication.

    Uses Authorization: Bearer <jwt_token> header.

    Requires PyJWT: pip install PyJWT

    Configuration in settings:
        SWIFTAPI = {
            "JWT_SECRET_KEY": "your-secret-key",
            "JWT_ALGORITHM": "HS256",
            "JWT_VERIFY_EXPIRATION": True,
        }
    """

    keyword = "Bearer"

    def authenticate(
        self,
        request: HttpRequest,
    ) -> tuple[AbstractUser, dict] | None:
        """Authenticate using JWT."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            return None

        token = parts[1]

        return self._authenticate_credentials(token)

    def _authenticate_credentials(
        self,
        token: str,
    ) -> tuple[AbstractUser, dict]:
        """Validate JWT and return user."""
        try:
            import jwt
        except ImportError:
            raise ValueError(
                "JWTAuthentication requires PyJWT. "
                "Install it with: pip install PyJWT"
            )

        from django.conf import settings as django_settings

        swiftapi_settings = getattr(django_settings, "SWIFTAPI", {})
        secret_key = swiftapi_settings.get(
            "JWT_SECRET_KEY",
            django_settings.SECRET_KEY,
        )
        algorithm = swiftapi_settings.get("JWT_ALGORITHM", "HS256")
        verify_exp = swiftapi_settings.get("JWT_VERIFY_EXPIRATION", True)

        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                options={"verify_exp": verify_exp},
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f"Invalid token: {e}")

        user = self._get_user(payload)

        return (user, payload)

    def _get_user(self, payload: dict) -> AbstractUser:
        """Get user from JWT payload."""
        User = get_user_model()

        user_id = payload.get("user_id") or payload.get("sub")

        if user_id is None:
            raise AuthenticationFailed("Token missing user identifier.")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found.")

        if not user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        return user

    def authenticate_header(self, request: HttpRequest) -> str:
        return 'Bearer realm="api"'

    @staticmethod
    def create_token(
        user: AbstractUser,
        extra_claims: dict | None = None,
        expiration_hours: int = 24,
    ) -> str:
        """
        Create a JWT token for a user.

        Args:
            user: User to create token for
            extra_claims: Additional claims to include
            expiration_hours: Token expiration in hours

        Returns:
            JWT token string
        """
        try:
            import jwt
        except ImportError:
            raise ValueError("PyJWT is required for JWT authentication.")

        import datetime

        from django.conf import settings as django_settings

        swiftapi_settings = getattr(django_settings, "SWIFTAPI", {})
        secret_key = swiftapi_settings.get(
            "JWT_SECRET_KEY",
            django_settings.SECRET_KEY,
        )
        algorithm = swiftapi_settings.get("JWT_ALGORITHM", "HS256")

        now = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            "user_id": user.pk,
            "iat": now,
            "exp": now + datetime.timedelta(hours=expiration_hours),
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, secret_key, algorithm=algorithm)


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication.

    Uses X-API-Key header or api_key query parameter.
    """

    header_name = "HTTP_X_API_KEY"
    query_param = "api_key"

    def authenticate(
        self,
        request: HttpRequest,
    ) -> tuple[AbstractUser, str] | None:
        """Authenticate using API key."""
        # Try header first
        api_key = request.META.get(self.header_name)

        # Try query parameter
        if not api_key:
            api_key = request.GET.get(self.query_param)

        if not api_key:
            return None

        return self._authenticate_credentials(api_key)

    def _authenticate_credentials(
        self,
        api_key: str,
    ) -> tuple[AbstractUser, str]:
        """Validate API key and return user."""
        # This should be overridden to use your API key storage
        raise NotImplementedError(
            "APIKeyAuthentication._authenticate_credentials() must be implemented. "
            "Override this method to validate API keys against your storage."
        )
