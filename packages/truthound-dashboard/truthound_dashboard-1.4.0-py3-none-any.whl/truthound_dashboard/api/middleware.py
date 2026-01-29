"""API middleware for security, logging, and rate limiting.

This module provides extensible middleware components for:
- Rate limiting with configurable strategies
- Security headers
- Request/response logging
- Authentication (optional)

The middleware uses the Chain of Responsibility pattern for
flexible composition.

Example:
    from truthound_dashboard.api.middleware import (
        RateLimitMiddleware,
        SecurityHeadersMiddleware,
        RequestLoggingMiddleware,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
    app.add_middleware(RequestLoggingMiddleware)
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from truthound_dashboard.core.exceptions import ErrorCode
from truthound_dashboard.core.i18n import SupportedLocale, detect_locale

logger = logging.getLogger(__name__)


# =============================================================================
# Locale Detection
# =============================================================================


class LocaleDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and set user locale from request.

    Detection priority:
    1. Query parameter: ?lang=ko
    2. Accept-Language header
    3. Default locale (English)

    The detected locale is stored in request.state.locale for use by
    API endpoints that need to return localized error messages.

    Example:
        # In endpoint
        locale = getattr(request.state, "locale", SupportedLocale.ENGLISH)
        message = get_message("source_not_found", locale)
    """

    def __init__(
        self,
        app: Any,
        default_locale: SupportedLocale = SupportedLocale.ENGLISH,
    ) -> None:
        """Initialize locale detection middleware.

        Args:
            app: ASGI application.
            default_locale: Default locale when detection fails.
        """
        super().__init__(app)
        self._default_locale = default_locale

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Detect locale and store in request state."""
        # Detect locale from request
        locale = detect_locale(request, default=self._default_locale)

        # Store in request state
        request.state.locale = locale

        # Process request
        response = await call_next(request)

        # Add Content-Language header
        response.headers["Content-Language"] = locale.value

        return response


# =============================================================================
# Rate Limiting
# =============================================================================


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        requests_per_minute: Maximum requests per minute.
        burst_size: Maximum burst size for token bucket.
        by_ip: Rate limit by IP address.
        by_path: Rate limit by path (in addition to IP).
        exclude_paths: Paths to exclude from rate limiting.
    """

    requests_per_minute: int = 60
    burst_size: int = 10
    by_ip: bool = True
    by_path: bool = False
    exclude_paths: list[str] = field(default_factory=lambda: ["/health", "/docs"])


class RateLimitStrategy(ABC):
    """Abstract base class for rate limiting strategies."""

    @abstractmethod
    def is_allowed(self, key: str) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed.

        Args:
            key: Rate limit key (e.g., IP address).

        Returns:
            Tuple of (allowed, info dict with remaining, reset_at, etc.)
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup expired entries."""
        ...


class SlidingWindowRateLimiter(RateLimitStrategy):
    """Sliding window rate limiter.

    Tracks requests in a sliding time window for smooth rate limiting.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        window_seconds: int = 60,
    ) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per window.
            window_seconds: Window size in seconds.
        """
        self._requests_per_minute = requests_per_minute
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def is_allowed(self, key: str) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed using sliding window."""
        now = time.time()
        window_start = now - self._window_seconds

        # Clean old requests
        self._requests[key] = [
            t for t in self._requests[key] if t > window_start
        ]

        current_count = len(self._requests[key])
        remaining = max(0, self._requests_per_minute - current_count)
        reset_at = int(now + self._window_seconds)

        info = {
            "limit": self._requests_per_minute,
            "remaining": remaining,
            "reset_at": reset_at,
        }

        if current_count >= self._requests_per_minute:
            return False, info

        # Record request
        self._requests[key].append(now)
        info["remaining"] = remaining - 1

        return True, info

    def cleanup(self) -> None:
        """Remove entries with no recent requests."""
        now = time.time()
        window_start = now - self._window_seconds

        keys_to_remove = []
        for key, timestamps in self._requests.items():
            if all(t <= window_start for t in timestamps):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._requests[key]


class TokenBucketRateLimiter(RateLimitStrategy):
    """Token bucket rate limiter.

    Allows burst traffic while maintaining average rate limit.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        bucket_size: int = 10,
    ) -> None:
        """Initialize token bucket rate limiter.

        Args:
            requests_per_minute: Token refill rate.
            bucket_size: Maximum tokens in bucket.
        """
        self._rate = requests_per_minute / 60.0  # tokens per second
        self._bucket_size = bucket_size
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_update)

    def is_allowed(self, key: str) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed using token bucket."""
        now = time.time()

        if key not in self._buckets:
            self._buckets[key] = (self._bucket_size - 1, now)
            return True, {
                "limit": self._bucket_size,
                "remaining": self._bucket_size - 1,
                "reset_at": int(now + (1 / self._rate)),
            }

        tokens, last_update = self._buckets[key]
        elapsed = now - last_update

        # Add tokens based on elapsed time
        tokens = min(self._bucket_size, tokens + elapsed * self._rate)

        info = {
            "limit": self._bucket_size,
            "remaining": int(tokens),
            "reset_at": int(now + ((self._bucket_size - tokens) / self._rate)),
        }

        if tokens < 1:
            return False, info

        # Consume token
        self._buckets[key] = (tokens - 1, now)
        info["remaining"] = int(tokens - 1)

        return True, info

    def cleanup(self) -> None:
        """Remove buckets that are full (no recent requests)."""
        keys_to_remove = []
        for key, (tokens, _) in self._buckets.items():
            if tokens >= self._bucket_size:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._buckets[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with configurable strategies.

    Limits request rate by IP address and optionally by path.
    """

    def __init__(
        self,
        app: Any,
        config: RateLimitConfig | None = None,
        strategy: RateLimitStrategy | None = None,
    ) -> None:
        """Initialize rate limit middleware.

        Args:
            app: ASGI application.
            config: Rate limit configuration.
            strategy: Rate limiting strategy. Defaults to sliding window.
        """
        super().__init__(app)
        self._config = config or RateLimitConfig()
        self._strategy = strategy or SlidingWindowRateLimiter(
            requests_per_minute=self._config.requests_per_minute
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request through rate limiter."""
        # Skip excluded paths
        if request.url.path in self._config.exclude_paths:
            return await call_next(request)

        # Build rate limit key
        key = self._build_key(request)

        # Check rate limit
        allowed, info = self._strategy.is_allowed(key)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {key}",
                extra={"path": request.url.path},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": ErrorCode.RATE_LIMIT_EXCEEDED.value,
                        "message": "Too many requests. Please try again later.",
                    },
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset_at"]),
                    "Retry-After": str(info["reset_at"] - int(time.time())),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset_at"])

        return response

    def _build_key(self, request: Request) -> str:
        """Build rate limit key from request."""
        parts = []

        if self._config.by_ip:
            client_ip = request.client.host if request.client else "unknown"
            parts.append(client_ip)

        if self._config.by_path:
            parts.append(request.url.path)

        return ":".join(parts) if parts else "global"


# =============================================================================
# Security Headers
# =============================================================================


@dataclass
class SecurityHeadersConfig:
    """Configuration for security headers.

    Attributes:
        content_type_options: X-Content-Type-Options value.
        frame_options: X-Frame-Options value.
        xss_protection: X-XSS-Protection value.
        referrer_policy: Referrer-Policy value.
        content_security_policy: Content-Security-Policy value.
        strict_transport_security: Strict-Transport-Security value.
        permissions_policy: Permissions-Policy value.
    """

    content_type_options: str = "nosniff"
    frame_options: str = "DENY"
    xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    content_security_policy: str | None = None
    strict_transport_security: str | None = None
    permissions_policy: str | None = None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    def __init__(
        self,
        app: Any,
        config: SecurityHeadersConfig | None = None,
    ) -> None:
        """Initialize security headers middleware.

        Args:
            app: ASGI application.
            config: Security headers configuration.
        """
        super().__init__(app)
        self._config = config or SecurityHeadersConfig()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Always add these headers
        response.headers["X-Content-Type-Options"] = self._config.content_type_options
        response.headers["X-Frame-Options"] = self._config.frame_options
        response.headers["X-XSS-Protection"] = self._config.xss_protection
        response.headers["Referrer-Policy"] = self._config.referrer_policy

        # Optionally add these headers
        if self._config.content_security_policy:
            response.headers["Content-Security-Policy"] = (
                self._config.content_security_policy
            )

        if self._config.strict_transport_security:
            response.headers["Strict-Transport-Security"] = (
                self._config.strict_transport_security
            )

        if self._config.permissions_policy:
            response.headers["Permissions-Policy"] = self._config.permissions_policy

        return response


# =============================================================================
# Request Logging
# =============================================================================


@dataclass
class RequestLogConfig:
    """Configuration for request logging.

    Attributes:
        log_headers: Whether to log request headers.
        log_body: Whether to log request body.
        exclude_paths: Paths to exclude from logging.
        sensitive_headers: Headers to mask in logs.
        max_body_length: Maximum body length to log.
    """

    log_headers: bool = False
    log_body: bool = False
    exclude_paths: list[str] = field(default_factory=lambda: ["/health"])
    sensitive_headers: list[str] = field(
        default_factory=lambda: ["authorization", "cookie", "x-api-key"]
    )
    max_body_length: int = 1000


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(
        self,
        app: Any,
        config: RequestLogConfig | None = None,
    ) -> None:
        """Initialize request logging middleware.

        Args:
            app: ASGI application.
            config: Request logging configuration.
        """
        super().__init__(app)
        self._config = config or RequestLogConfig()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Log request and response."""
        # Skip excluded paths
        if request.url.path in self._config.exclude_paths:
            return await call_next(request)

        # Generate request ID
        request_id = hashlib.sha256(
            f"{time.time()}{request.client}".encode()
        ).hexdigest()[:8]

        start_time = time.time()

        # Build log context
        log_context = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        }

        if self._config.log_headers:
            log_context["headers"] = self._mask_headers(dict(request.headers))

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Started",
            extra=log_context,
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            log_context["status_code"] = response.status_code
            log_context["duration_ms"] = duration_ms

            log_level = logging.INFO
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING

            logger.log(
                log_level,
                f"[{request_id}] {request.method} {request.url.path} - "
                f"{response.status_code} ({duration_ms}ms)",
                extra=log_context,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_context["duration_ms"] = duration_ms
            log_context["error"] = str(e)

            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error ({duration_ms}ms): {e}",
                extra=log_context,
                exc_info=True,
            )
            raise

    def _mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Mask sensitive headers."""
        masked = {}
        for key, value in headers.items():
            if key.lower() in self._config.sensitive_headers:
                masked[key] = "***"
            else:
                masked[key] = value
        return masked


# =============================================================================
# Authentication Middleware
# =============================================================================


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Optional basic authentication middleware.

    Only active when auth_enabled is True in settings.
    """

    def __init__(
        self,
        app: Any,
        password: str | None = None,
        exclude_paths: list[str] | None = None,
    ) -> None:
        """Initialize basic auth middleware.

        Args:
            app: ASGI application.
            password: Password for authentication.
            exclude_paths: Paths to exclude from authentication.
        """
        super().__init__(app)
        self._password = password
        self._exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Authenticate request if password is set."""
        # Skip if no password configured
        if not self._password:
            return await call_next(request)

        # Skip excluded paths
        if any(request.url.path.startswith(p) for p in self._exclude_paths):
            return await call_next(request)

        # Check authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized_response()

        # Parse Basic auth
        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "basic":
                return self._unauthorized_response()

            import base64
            decoded = base64.b64decode(credentials).decode("utf-8")
            _, password = decoded.split(":", 1)

            if password != self._password:
                return self._unauthorized_response()

        except (ValueError, UnicodeDecodeError):
            return self._unauthorized_response()

        return await call_next(request)

    def _unauthorized_response(self) -> JSONResponse:
        """Create 401 Unauthorized response."""
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": ErrorCode.AUTHENTICATION_REQUIRED.value,
                    "message": "Authentication required",
                },
            },
            headers={"WWW-Authenticate": "Basic realm='truthound-dashboard'"},
        )


# =============================================================================
# Notification Throttling Middleware
# =============================================================================


@dataclass
class NotificationThrottleConfig:
    """Configuration for notification-specific throttling.

    This middleware integrates with the notification throttling system
    to provide endpoint-specific rate limiting for notification operations.

    Attributes:
        enabled: Whether throttling is enabled.
        per_minute: Default requests per minute for notification endpoints.
        per_hour: Default requests per hour for notification endpoints.
        per_day: Default requests per day for notification endpoints.
        burst_allowance: Burst allowance factor (e.g., 1.5 = 50% extra burst).
        endpoint_overrides: Per-endpoint limit overrides.
    """

    enabled: bool = True
    per_minute: int = 60
    per_hour: int = 500
    per_day: int = 5000
    burst_allowance: float = 1.5
    endpoint_overrides: dict[str, dict[str, int]] = field(default_factory=dict)


class NotificationThrottleMiddleware(BaseHTTPMiddleware):
    """Middleware for notification-specific throttling.

    Provides fine-grained rate limiting for notification operations with:
    - Per-minute, per-hour, and per-day limits
    - Endpoint-specific overrides
    - Burst allowance
    - Integration with notification throttling metrics

    Response Headers:
        X-RateLimit-Limit: Maximum requests in current window
        X-RateLimit-Remaining: Remaining requests in current window
        X-RateLimit-Reset: Unix timestamp when the limit resets
        X-RateLimit-Window: Current limiting window (minute/hour/day)
        Retry-After: Seconds until the limit resets (on 429 only)
    """

    NOTIFICATION_PATHS = [
        "/api/v1/notifications",
    ]

    def __init__(
        self,
        app: Any,
        config: NotificationThrottleConfig | None = None,
    ) -> None:
        """Initialize notification throttle middleware.

        Args:
            app: ASGI application.
            config: Throttling configuration.
        """
        super().__init__(app)
        self._config = config or NotificationThrottleConfig()

        # Separate counters for minute/hour/day windows
        self._minute_counts: dict[str, list[float]] = defaultdict(list)
        self._hour_counts: dict[str, list[float]] = defaultdict(list)
        self._day_counts: dict[str, list[float]] = defaultdict(list)

        # Metrics
        self._total_requests = 0
        self._throttled_requests = 0

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with notification-specific throttling."""
        # Only apply to notification endpoints
        if not self._config.enabled or not self._is_notification_endpoint(request.url.path):
            return await call_next(request)

        # Get client key
        client_ip = request.client.host if request.client else "unknown"
        key = f"notif:{client_ip}"

        self._total_requests += 1

        # Get limits for this endpoint
        limits = self._get_limits(request.url.path)

        # Check all windows
        now = time.time()
        allowed, info = self._check_limits(key, limits, now)

        if not allowed:
            self._throttled_requests += 1
            logger.warning(
                f"Notification throttle exceeded for {key}",
                extra={
                    "path": request.url.path,
                    "window": info["window"],
                    "limit": info["limit"],
                },
            )

            retry_after = info["reset_at"] - int(now)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": ErrorCode.RATE_LIMIT_EXCEEDED.value,
                        "message": f"Rate limit exceeded for {info['window']} window. "
                                   f"Try again in {retry_after} seconds.",
                        "details": {
                            "window": info["window"],
                            "limit": info["limit"],
                            "remaining": 0,
                            "reset_at": info["reset_at"],
                        },
                    },
                },
                headers=self._build_headers(info, retry_after),
            )

        # Record request
        self._record_request(key, now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers.update(self._build_headers(info))

        return response

    def _is_notification_endpoint(self, path: str) -> bool:
        """Check if path is a notification endpoint."""
        return any(path.startswith(p) for p in self.NOTIFICATION_PATHS)

    def _get_limits(self, path: str) -> dict[str, int]:
        """Get rate limits for a specific path."""
        # Check for endpoint-specific overrides
        for pattern, limits in self._config.endpoint_overrides.items():
            if path.startswith(pattern):
                return {
                    "minute": limits.get("per_minute", self._config.per_minute),
                    "hour": limits.get("per_hour", self._config.per_hour),
                    "day": limits.get("per_day", self._config.per_day),
                }

        # Return default limits with burst allowance
        burst = self._config.burst_allowance
        return {
            "minute": int(self._config.per_minute * burst),
            "hour": int(self._config.per_hour * burst),
            "day": int(self._config.per_day * burst),
        }

    def _check_limits(
        self,
        key: str,
        limits: dict[str, int],
        now: float,
    ) -> tuple[bool, dict[str, Any]]:
        """Check all rate limit windows.

        Returns:
            Tuple of (allowed, info dict).
        """
        # Clean old entries
        self._cleanup_window(key, now)

        # Check minute limit first (strictest)
        minute_count = len(self._minute_counts[key])
        if minute_count >= limits["minute"]:
            return False, {
                "window": "minute",
                "limit": limits["minute"],
                "remaining": 0,
                "reset_at": int(now + 60 - (now % 60)),
            }

        # Check hour limit
        hour_count = len(self._hour_counts[key])
        if hour_count >= limits["hour"]:
            return False, {
                "window": "hour",
                "limit": limits["hour"],
                "remaining": 0,
                "reset_at": int(now + 3600 - (now % 3600)),
            }

        # Check day limit
        day_count = len(self._day_counts[key])
        if day_count >= limits["day"]:
            return False, {
                "window": "day",
                "limit": limits["day"],
                "remaining": 0,
                "reset_at": int(now + 86400 - (now % 86400)),
            }

        # All windows have capacity - return most restrictive remaining
        minute_remaining = limits["minute"] - minute_count
        hour_remaining = limits["hour"] - hour_count
        day_remaining = limits["day"] - day_count

        # Find the most restrictive window
        if minute_remaining <= hour_remaining and minute_remaining <= day_remaining:
            return True, {
                "window": "minute",
                "limit": limits["minute"],
                "remaining": minute_remaining - 1,
                "reset_at": int(now + 60 - (now % 60)),
            }
        elif hour_remaining <= day_remaining:
            return True, {
                "window": "hour",
                "limit": limits["hour"],
                "remaining": hour_remaining - 1,
                "reset_at": int(now + 3600 - (now % 3600)),
            }
        else:
            return True, {
                "window": "day",
                "limit": limits["day"],
                "remaining": day_remaining - 1,
                "reset_at": int(now + 86400 - (now % 86400)),
            }

    def _record_request(self, key: str, now: float) -> None:
        """Record a request in all windows."""
        self._minute_counts[key].append(now)
        self._hour_counts[key].append(now)
        self._day_counts[key].append(now)

    def _cleanup_window(self, key: str, now: float) -> None:
        """Remove expired entries from all windows."""
        minute_start = now - 60
        hour_start = now - 3600
        day_start = now - 86400

        self._minute_counts[key] = [
            t for t in self._minute_counts[key] if t > minute_start
        ]
        self._hour_counts[key] = [
            t for t in self._hour_counts[key] if t > hour_start
        ]
        self._day_counts[key] = [
            t for t in self._day_counts[key] if t > day_start
        ]

    def _build_headers(
        self,
        info: dict[str, Any],
        retry_after: int | None = None,
    ) -> dict[str, str]:
        """Build rate limit response headers."""
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(max(0, info["remaining"])),
            "X-RateLimit-Reset": str(info["reset_at"]),
            "X-RateLimit-Window": info["window"],
        }

        if retry_after is not None:
            headers["Retry-After"] = str(max(0, retry_after))

        return headers

    def get_metrics(self) -> dict[str, Any]:
        """Get throttling metrics.

        Returns:
            Dictionary with throttling statistics.
        """
        return {
            "total_requests": self._total_requests,
            "throttled_requests": self._throttled_requests,
            "throttle_rate": (
                self._throttled_requests / self._total_requests * 100
                if self._total_requests > 0 else 0
            ),
            "active_keys": len(self._minute_counts),
        }


# =============================================================================
# Middleware Setup Helper
# =============================================================================


def setup_middleware(app: Any) -> None:
    """Configure all middleware for the application.

    Args:
        app: FastAPI application instance.
    """
    from truthound_dashboard.config import get_settings

    settings = get_settings()

    # Add middleware in reverse order (last added = first executed)

    # Request logging (always enabled)
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting (general)
    rate_limit_config = RateLimitConfig(
        requests_per_minute=120,
        exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/api/openapi.json"],
    )
    app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

    # Notification-specific throttling (more granular)
    notif_throttle_config = NotificationThrottleConfig(
        per_minute=60,
        per_hour=500,
        per_day=5000,
        burst_allowance=1.5,
        endpoint_overrides={
            # Higher limits for read operations
            "/api/v1/notifications/routing/rules": {
                "per_minute": 120,
                "per_hour": 1000,
            },
            # Lower limits for write operations
            "/api/v1/notifications/escalation/incidents": {
                "per_minute": 30,
                "per_hour": 200,
            },
        },
    )
    app.add_middleware(NotificationThrottleMiddleware, config=notif_throttle_config)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Basic auth (optional)
    if settings.auth_enabled and settings.auth_password:
        app.add_middleware(
            BasicAuthMiddleware,
            password=settings.auth_password,
        )

    # Locale detection (runs first, so it's available to all other middleware)
    app.add_middleware(LocaleDetectionMiddleware)

    logger.info("Middleware configured successfully")
