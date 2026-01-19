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

        # Skip authentication for static files, root, docs, and health check
        path = request.url.path
        if (path.startswith("/static/") or
            path == "/" or
            path == "/health" or
            path == "/docs" or
            path == "/openapi.json"):
            await self.app(scope, receive, send)
            return

        # Check authentication for API endpoints
        if path.startswith("/diagnose") or path.startswith("/followup") or path.startswith("/api/"):
            try:
                await self._check_authentication(request)
                await self._check_referrer(request)
            except HTTPException as exc:
                # Convert HTTPException to JSON response
                response = JSONResponse(
                    status_code=exc.status_code,
                    content={"error": exc.detail}
                )
                await response(scope, receive, send)
                return
            except Exception as exc:
                # Log unexpected errors
                import traceback
                print(f"Security middleware error: {exc}")
                print(traceback.format_exc())
                response = JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error"}
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    async def _check_authentication(self, request: Request):
        """Validate API password from request headers."""
        from urllib.parse import unquote

        auth_header = request.headers.get("X-API-Password")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide X-API-Password header."
            )

        # Decode URL-encoded password (frontend encodes special chars)
        decoded_password = unquote(auth_header)

        if decoded_password != settings.api_password:
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
