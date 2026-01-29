"""
SwiftAPI Throttling System.

Rate limiting support for API endpoints.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from django.core.cache import cache

from swiftapi.exceptions import Throttled

if TYPE_CHECKING:
    from django.http import HttpRequest

    from swiftapi.viewsets import ViewSet


class BaseThrottle:
    """
    Base class for throttling.

    Throttles limit the rate of API requests to protect
    against abuse and ensure fair resource usage.
    """

    def allow_request(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        """
        Check if the request should be allowed.

        Args:
            request: The HTTP request
            view: The ViewSet instance

        Returns:
            True if request is allowed, False if throttled
        """
        raise NotImplementedError

    def wait(self) -> float | None:
        """
        Return the number of seconds to wait before retrying.

        Returns:
            Seconds to wait, or None if unknown
        """
        return None

    def get_ident(self, request: HttpRequest) -> str:
        """
        Get a unique identifier for the request source.

        Default implementation uses IP address.
        """
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR", "")


class SimpleRateThrottle(BaseThrottle):
    """
    Simple rate throttling based on request count per time window.

    Subclass and set the `rate` attribute:
    - "100/day" - 100 requests per day
    - "1000/hour" - 1000 requests per hour
    - "100/minute" - 100 requests per minute
    - "1/second" - 1 request per second
    """

    rate: str | None = None
    cache_format = "throttle_%(scope)s_%(ident)s"
    scope = "default"

    # Time windows in seconds
    THROTTLE_RATES = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }

    def __init__(self) -> None:
        self.num_requests: int = 0
        self.duration: int = 0
        self.history: list[float] = []

        if self.rate:
            self._parse_rate(self.rate)

    def _parse_rate(self, rate: str) -> None:
        """Parse rate string like '100/hour'."""
        try:
            num, period = rate.split("/")
            self.num_requests = int(num)
            self.duration = self.THROTTLE_RATES.get(period, 0)
        except (ValueError, AttributeError):
            self.num_requests = 0
            self.duration = 0

    def allow_request(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        """Check if request should be allowed based on rate limit."""
        if self.num_requests == 0:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = cache.get(self.key, [])
        self.now = time.time()

        # Remove old entries outside the window
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return False

        return self.throttle_success()

    def throttle_success(self) -> bool:
        """Record successful request."""
        self.history.insert(0, self.now)
        cache.set(self.key, self.history, self.duration)
        return True

    def get_cache_key(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> str | None:
        """Get the cache key for this request."""
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def wait(self) -> float | None:
        """Calculate seconds until next request is allowed."""
        if self.history:
            remaining = self.duration - (self.now - self.history[-1])
            return max(0, remaining)
        return None


class AnonRateThrottle(SimpleRateThrottle):
    """
    Throttle anonymous (unauthenticated) users by IP.

    Configure rate in settings:
        SWIFTAPI = {
            "DEFAULT_THROTTLE_RATES": {
                "anon": "100/day",
            }
        }
    """

    scope = "anon"

    def __init__(self) -> None:
        super().__init__()
        self._load_rate_from_settings()

    def _load_rate_from_settings(self) -> None:
        """Load rate from SWIFTAPI settings."""
        from swiftapi.conf import settings

        rates = settings.DEFAULT_THROTTLE_RATES
        if self.scope in rates:
            self._parse_rate(rates[self.scope])

    def get_cache_key(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> str | None:
        """Only throttle unauthenticated requests."""
        if hasattr(request, "user") and request.user.is_authenticated:
            return None  # Don't throttle authenticated users

        return super().get_cache_key(request, view)


class UserRateThrottle(SimpleRateThrottle):
    """
    Throttle authenticated users by user ID.

    Configure rate in settings:
        SWIFTAPI = {
            "DEFAULT_THROTTLE_RATES": {
                "user": "1000/day",
            }
        }
    """

    scope = "user"

    def __init__(self) -> None:
        super().__init__()
        self._load_rate_from_settings()

    def _load_rate_from_settings(self) -> None:
        """Load rate from SWIFTAPI settings."""
        from swiftapi.conf import settings

        rates = settings.DEFAULT_THROTTLE_RATES
        if self.scope in rates:
            self._parse_rate(rates[self.scope])

    def get_cache_key(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> str | None:
        """Only throttle authenticated requests."""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None  # Don't throttle anonymous users

        ident = str(request.user.pk)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class ScopedRateThrottle(SimpleRateThrottle):
    """
    Throttle by a custom scope defined on the ViewSet.

    Usage:
        class MyViewSet(ViewSet):
            throttle_scope = "premium"

        SWIFTAPI = {
            "DEFAULT_THROTTLE_RATES": {
                "premium": "10000/day",
            }
        }
    """

    scope_attr = "throttle_scope"

    def __init__(self) -> None:
        super().__init__()

    def allow_request(
        self,
        request: HttpRequest,
        view: ViewSet,
    ) -> bool:
        """Check request with view-specific scope."""
        self.scope = getattr(view, self.scope_attr, None)

        if not self.scope:
            return True

        self._load_rate_from_settings()
        return super().allow_request(request, view)

    def _load_rate_from_settings(self) -> None:
        """Load rate from SWIFTAPI settings."""
        from swiftapi.conf import settings

        rates = settings.DEFAULT_THROTTLE_RATES
        if self.scope in rates:
            self._parse_rate(rates[self.scope])


def check_throttles(
    request: HttpRequest,
    view: ViewSet,
) -> None:
    """
    Check all throttles for a ViewSet.

    Raises Throttled if any throttle denies the request.
    """
    from swiftapi.conf import import_from_string, settings

    throttle_classes = getattr(view, "throttle_classes", None)
    if throttle_classes is None:
        throttle_classes = [
            import_from_string(path, "throttle_classes")
            for path in settings.DEFAULT_THROTTLE_CLASSES
        ]

    for throttle_class in throttle_classes:
        if isinstance(throttle_class, str):
            throttle_class = import_from_string(throttle_class, "throttle_classes")

        throttle = throttle_class()

        if not throttle.allow_request(request, view):
            wait = throttle.wait()
            raise Throttled(wait=wait)
