"""
Custom Exception Classes
Provides domain-specific exceptions for better error handling
"""

from typing import Any, Optional, Dict


class NodeRushException(Exception):
    """Base exception for all NodeRush errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization Errors

class AuthenticationError(NodeRushException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
            details=details
        )


class AuthorizationError(NodeRushException):
    """Raised when user lacks required permissions"""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_FAILED",
            details=details
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            details={"error_type": "token_expired"}
        )


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(
            message=message,
            details={"error_type": "invalid_token"}
        )


class SessionExpiredError(AuthenticationError):
    """Raised when Redis session has expired"""

    def __init__(self, message: str = "Session expired. Please login again."):
        super().__init__(
            message=message,
            details={"error_type": "session_expired"}
        )


# Resource Errors

class ResourceNotFoundError(NodeRushException):
    """Raised when a requested resource is not found"""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None
    ):
        msg = message or f"{resource_type} not found"
        if resource_id:
            msg = f"{resource_type} with ID '{resource_id}' not found"

        super().__init__(
            message=msg,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class ResourceAlreadyExistsError(NodeRushException):
    """Raised when trying to create a resource that already exists"""

    def __init__(
        self,
        resource_type: str,
        identifier: str,
        message: Optional[str] = None
    ):
        msg = message or f"{resource_type} already exists"

        super().__init__(
            message=msg,
            status_code=409,
            error_code="RESOURCE_ALREADY_EXISTS",
            details={
                "resource_type": resource_type,
                "identifier": identifier
            }
        )


# Validation Errors

class ValidationError(NodeRushException):
    """Raised when input validation fails"""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        validation_details = details or {}
        if field:
            validation_details["field"] = field

        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=validation_details
        )


class InvalidInputError(ValidationError):
    """Raised when input data is invalid"""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Invalid {field}: {message}",
            field=field
        )


# Rate Limiting Errors

class RateLimitExceededError(NodeRushException):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        resource: str,
        limit: int,
        window: int,
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=f"Rate limit exceeded for {resource}. Limit: {limit} requests per {window} seconds.",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "resource": resource,
                "limit": limit,
                "window": window,
                "retry_after": retry_after or window
            }
        )


class QuotaExceededError(NodeRushException):
    """Raised when user quota is exceeded"""

    def __init__(
        self,
        quota_type: str,
        limit: int,
        current: int
    ):
        super().__init__(
            message=f"{quota_type} quota exceeded. Limit: {limit}, Current: {current}",
            status_code=429,
            error_code="QUOTA_EXCEEDED",
            details={
                "quota_type": quota_type,
                "limit": limit,
                "current": current
            }
        )


# Service Errors

class ServiceUnavailableError(NodeRushException):
    """Raised when an external service is unavailable"""

    def __init__(self, service_name: str, message: Optional[str] = None):
        msg = message or f"{service_name} is currently unavailable"

        super().__init__(
            message=msg,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service_name}
        )


class DatabaseError(NodeRushException):
    """Raised when database operation fails"""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details
        )


class RedisError(NodeRushException):
    """Raised when Redis operation fails"""

    def __init__(self, message: str = "Redis operation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="REDIS_ERROR",
            details=details
        )


# AI/LangGraph Errors

class AIGenerationError(NodeRushException):
    """Raised when AI generation fails"""

    def __init__(
        self,
        agent_name: str,
        message: str = "AI generation failed",
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=f"{agent_name}: {message}",
            status_code=500,
            error_code="AI_GENERATION_ERROR",
            details={
                "agent": agent_name,
                **(details or {})
            }
        )


class TokenLimitExceededError(NodeRushException):
    """Raised when AI token limit is exceeded"""

    def __init__(
        self,
        tokens_used: int,
        tokens_limit: int,
        message: Optional[str] = None
    ):
        msg = message or f"Token limit exceeded. Used: {tokens_used}, Limit: {tokens_limit}"

        super().__init__(
            message=msg,
            status_code=429,
            error_code="TOKEN_LIMIT_EXCEEDED",
            details={
                "tokens_used": tokens_used,
                "tokens_limit": tokens_limit
            }
        )


# Configuration Errors

class ConfigurationError(NodeRushException):
    """Raised when configuration is invalid or missing"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


# Integration Errors

class IntegrationError(NodeRushException):
    """Raised when external integration fails"""

    def __init__(
        self,
        integration_name: str,
        message: str,
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=f"{integration_name} integration error: {message}",
            status_code=502,
            error_code="INTEGRATION_ERROR",
            details={
                "integration": integration_name,
                **(details or {})
            }
        )
