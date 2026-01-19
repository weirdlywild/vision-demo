"""
Security middleware for authentication, rate limiting, and referrer checking.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Callable
from app.config import settings
import time


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class SecurityMiddleware:
    """Middleware for authentication and referrer checking."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Skip authentication for static files and root
        path = request.url.path
        if path.startswith("/static/") or path == "/":
            await self.app(scope, receive, send)
            return

        # Check authentication for API endpoints
        if path.startswith("/diagnose") or path.startswith("/api/"):
            await self._check_authentication(request)
            await self._check_referrer(request)

        await self.app(scope, receive, send)

    async def _check_authentication(self, request: Request):
        """Validate API password from request headers."""
        auth_header = request.headers.get("X-API-Password")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide X-API-Password header."
            )

        if auth_header != settings.api_password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials."
            )

    async def _check_referrer(self, request: Request):
        """Check if request comes from allowed origin."""
        # Allow requests from localhost and 127.0.0.1
        origin = request.headers.get("origin", "")
        referer = request.headers.get("referer", "")
        host = request.headers.get("host", "")

        # Extract hostname from origin/referer
        allowed_hosts = ["localhost", "127.0.0.1", host]

        # If origin or referer exists, validate it
        if origin or referer:
            source = origin or referer
            is_allowed = any(allowed_host in source for allowed_host in allowed_hosts)

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Request from unauthorized origin."
                )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Please try again in a minute.",
            "retry_after": 60
        }
    )
