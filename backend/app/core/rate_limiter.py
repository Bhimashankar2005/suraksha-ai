import time
import threading
from typing import Dict, List, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

class InMemoryRateLimiter:
    """
    Zero-cloud, high-performance in-memory sliding-window rate limiter.
    Provides thread-safe IP/endpoint rate limiting without requiring external Redis.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._storage: Dict[str, List[float]] = {}
        self._max_tracked_keys = 20000

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Evaluates whether a request with the given key is allowed under the sliding window.
        Returns:
            (allowed: bool, retry_after_seconds: int, remaining_requests: int)
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Auto-clean when storage grows excessively
            if len(self._storage) > self._max_tracked_keys:
                self._cleanup_stale_keys(now)

            timestamps = self._storage.get(key, [])
            # Keep only timestamps inside the current sliding window
            valid_timestamps = [t for t in timestamps if t > window_start]

            if len(valid_timestamps) >= max_requests:
                # Oldest timestamp within window determines when a slot opens up
                oldest_in_window = valid_timestamps[0]
                retry_after = max(1, int(oldest_in_window + window_seconds - now))
                self._storage[key] = valid_timestamps
                return False, retry_after, 0

            # Record current request timestamp
            valid_timestamps.append(now)
            self._storage[key] = valid_timestamps
            remaining = max(0, max_requests - len(valid_timestamps))
            return True, 0, remaining

    def _cleanup_stale_keys(self, now: float):
        """Removes keys with no recent activity older than 1 hour."""
        cutoff = now - 3600
        keys_to_remove = [
            k for k, timestamps in self._storage.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for k in keys_to_remove:
            del self._storage[k]

    def reset(self):
        """Clears all stored rate limits. Useful for automated tests and SOC resets."""
        with self._lock:
            self._storage.clear()

# Global rate limiter instance
limiter = InMemoryRateLimiter()

# Route rate limit profiles
RATE_LIMIT_RULES = [
    # (path_prefix, max_requests, window_seconds, rule_name)
    ("/api/v1/auth/login", 10, 60, "auth_login"),
    ("/api/v1/auth/register", 10, 60, "auth_register"),
    ("/api/v1/scam/scan", 60, 60, "scam_scan"),
    ("/api/v1/url/scan", 60, 60, "url_scan"),
    ("/api/v1/image/scan", 60, 60, "image_scan"),
    ("/api/v1/deepfake/analyze", 60, 60, "deepfake_scan"),
    ("/api/v1/privacy/scan-text", 60, 60, "privacy_scan"),
]

# Excluded paths that are never rate limited
EXCLUDED_PREFIXES = [
    "/api/v1/health",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/redoc",
    "/docs",
    "/redoc",
    "/openapi.json"
]

def create_rate_limit_exceeded_response(retry_after: int, max_requests: int) -> JSONResponse:
    """Builds standard 429 Too Many Requests response with retry and helpline guidance."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded. Too many requests. Please try again in {retry_after} seconds.",
            "retry_after_seconds": retry_after,
            "helpline_notice": "In case of urgent cyber fraud emergency, please contact National Cyber Crime Helpline 1930 directly or visit https://cybercrime.gov.in."
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": "0"
        }
    )

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    FastAPI / Starlette middleware enforcing in-memory rate limiting.
    Emits standard HTTP 429 Too Many Requests responses and Retry-After headers.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Root and health checks bypass rate limiting
        if path == "/" or any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            return await call_next(request)

        # Allow test suites to bypass rate limiting via test header if needed
        if request.headers.get("X-Test-Bypass-Rate-Limit") == "true":
            return await call_next(request)

        # Extract client IP
        client_ip = request.client.host if request.client else "unknown_client"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # Match against specific route rule or apply global API fallback
        rule_name = "global_api"
        max_requests = 120
        window_seconds = 60

        for prefix, max_req, win_sec, name in RATE_LIMIT_RULES:
            if path.startswith(prefix):
                rule_name = name
                max_requests = max_req
                window_seconds = win_sec
                break

        key = f"{rule_name}:{client_ip}"
        allowed, retry_after, remaining = limiter.is_allowed(key, max_requests, window_seconds)

        if not allowed:
            return create_rate_limit_exceeded_response(retry_after, max_requests)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

