"""
CORS and Security Middleware
Implements comprehensive security headers and request/response logging
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
from typing import Callable

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses
    Implements OWASP security best practices
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy (CSP)
        # Note: Adjust based on your frontend needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all incoming requests and outgoing responses
    Tracks request duration and adds unique request ID
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Get client info
        client_ip = request.client.host if request.client else "unknown"

        # Create request logger with context
        request_logger = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            ip_address=client_ip
        )

        # Log request
        start_time = time.time()
        request_logger.info(
            f"Request started: {request.method} {request.url.path}",
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer")
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            request_logger.info(
                f"Request completed: {request.method} {request.url.path}",
                status_code=response.status_code,
                duration=round(duration, 3)
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            request_logger.error(
                f"Request failed: {request.method} {request.url.path}",
                error=str(e),
                error_type=type(e).__name__,
                duration=round(duration, 3)
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Basic rate limiting middleware
    TODO: Integrate with Redis for distributed rate limiting
    """

    def __init__(self, app: ASGIApp, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = {}  # In-memory storage (should use Redis in production)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"

        # TODO: Implement Redis-based rate limiting
        # For now, just pass through
        # This will be implemented in Day 2 Task 3 (Upstash Redis setup)

        return await call_next(request)


def setup_cors_middleware(app, origins: list):
    """
    Setup CORS middleware with proper configuration
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # List of allowed origins
        allow_credentials=True,  # Allow cookies/auth headers
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Allowed HTTP methods
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-API-Key",
        ],  # Allowed headers
        expose_headers=[
            "X-Request-ID",
            "X-Total-Count",
        ],  # Headers exposed to frontend
        max_age=600,  # Cache preflight requests for 10 minutes
    )

    logger.info(f"CORS middleware configured with origins: {origins}")


def setup_security_middleware(app):
    """
    Setup all security-related middleware
    """
    # Add middleware in order (executed in reverse order)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    # app.add_middleware(RateLimitMiddleware)  # Enable when Redis is ready

    logger.info("Security middleware configured")
