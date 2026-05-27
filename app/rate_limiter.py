"""
IP-based rate limiting using slowapi.

Provides a shared Limiter instance and a custom 429 error handler
that returns a JSON response consistent with the rest of the API.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ── Limiter instance (imported by main.py and route modules) ────────────
limiter = Limiter(key_func=get_remote_address)

# Default rate string for API endpoints
DEFAULT_RATE = "10/minute"


def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """
    Custom handler for 429 Too Many Requests.

    Returns a friendly JSON error instead of the default plain-text response.
    """
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Rate limit exceeded. Please wait a moment and try again.",
            "detail": str(exc.detail),
        },
    )
