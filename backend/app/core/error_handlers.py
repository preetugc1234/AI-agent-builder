"""
Centralized Error Handlers
Custom exception handlers for FastAPI application
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
import logging
from typing import Union

from app.core.exceptions import NodeRushException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def noderush_exception_handler(request: Request, exc: NodeRushException) -> JSONResponse:
    """
    Handler for custom NodeRush exceptions

    Returns structured error response with status code, error code, and details
    """

    # Log the error
    logger.error(
        f"NodeRush exception: {exc.error_code}",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    # Return structured error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for HTTP exceptions (404, 403, etc.)
    """

    # Log the error
    logger.warning(
        f"HTTP exception: {exc.status_code}",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )

    # Return structured error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, PydanticValidationError]
) -> JSONResponse:
    """
    Handler for Pydantic validation errors

    Formats validation errors in a user-friendly way
    """

    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    # Log the error
    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=errors,
    )

    # Return structured error response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "errors": errors,
            "path": str(request.url.path),
        },
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler for database errors

    Hides internal database details from users for security
    """

    # Log the full error (with traceback)
    logger.exception(
        "Database error",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
    )

    # Return generic error response (don't expose internal DB details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DATABASE_ERROR",
            "message": "A database error occurred. Please try again later.",
            "path": str(request.url.path),
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions

    Logs the full error and returns a generic error response
    """

    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)

    # Log the full exception with traceback
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        request_id=request_id,
        error_type=type(exc).__name__,
        error_message=str(exc),
    )

    # Determine if we should expose the error message
    from app.core.config import settings
    expose_error = settings.DEBUG

    # Return generic error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc) if expose_error else "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
            "path": str(request.url.path),
        },
    )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI application

    Args:
        app: FastAPI application instance
    """

    # Custom NodeRush exceptions
    app.add_exception_handler(NodeRushException, noderush_exception_handler)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)

    # Database errors
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)

    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, global_exception_handler)

    logger.info("Error handlers registered")
