"""
Audit Logging Service
Tracks security events, user actions, and system events for compliance and monitoring
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.logging_config import get_logger
from app.services.redis_service import redis_service

logger = get_logger(__name__)


class AuditEventType:
    """Audit event type constants"""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_EXPIRED = "token_expired"
    SESSION_EXPIRED = "session_expired"

    # Authorization events
    PERMISSION_DENIED = "permission_denied"
    TIER_RESTRICTION = "tier_restriction"

    # Resource events
    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    RESOURCE_ACCESSED = "resource_accessed"

    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"

    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    INVALID_TOKEN = "invalid_token"
    CSRF_VIOLATION = "csrf_violation"

    # System events
    SYSTEM_ERROR = "system_error"
    DATABASE_ERROR = "database_error"
    REDIS_ERROR = "redis_error"


class AuditService:
    """
    Service for logging audit events

    Logs are written to:
    1. Application logs (immediate)
    2. Redis (for real-time monitoring)
    3. Database (for long-term storage and compliance)
    """

    @staticmethod
    async def log_event(
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
        db: Optional[AsyncSession] = None
    ):
        """
        Log an audit event

        Args:
            event_type: Type of event (use AuditEventType constants)
            user_id: User ID (if applicable)
            ip_address: Client IP address
            details: Additional event details
            severity: Event severity (info, warning, error, critical)
            db: Database session (optional, for DB logging)
        """

        # Prepare event data
        event_data = {
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": severity,
        }

        # Log to application logs
        log_method = getattr(logger, severity, logger.info)
        log_method(
            f"Audit event: {event_type}",
            **event_data
        )

        # Log to Redis for real-time monitoring
        try:
            await redis_service.cache_set(
                key=f"audit:{event_type}:{datetime.utcnow().timestamp()}",
                value=event_data,
                expire_seconds=86400  # Keep for 24 hours
            )
        except Exception as e:
            logger.error(f"Failed to log audit event to Redis: {e}")

        # Log to database for long-term storage (if session provided)
        if db:
            try:
                await AuditService._log_to_database(db, event_data)
            except Exception as e:
                logger.error(f"Failed to log audit event to database: {e}")

        # Check for suspicious patterns
        await AuditService._check_suspicious_activity(event_type, user_id, ip_address)

    @staticmethod
    async def _log_to_database(db: AsyncSession, event_data: Dict):
        """Log event to database (if security_logs table exists)"""
        try:
            # Check if table exists first
            query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'security_logs'
                )
            """)
            result = await db.execute(query)
            table_exists = result.scalar()

            if table_exists:
                # Insert audit log
                insert_query = text("""
                    INSERT INTO security_logs
                    (event_type, user_id, ip_address, details, severity, created_at)
                    VALUES (:event_type, :user_id, :ip_address, :details, :severity, :created_at)
                """)

                await db.execute(insert_query, {
                    "event_type": event_data["event_type"],
                    "user_id": event_data["user_id"],
                    "ip_address": event_data["ip_address"],
                    "details": str(event_data["details"]),  # Convert to JSON string
                    "severity": event_data["severity"],
                    "created_at": datetime.utcnow()
                })
                await db.commit()

        except Exception as e:
            logger.warning(f"Could not log to database (table may not exist): {e}")

    @staticmethod
    async def _check_suspicious_activity(
        event_type: str,
        user_id: Optional[str],
        ip_address: Optional[str]
    ):
        """
        Check for suspicious activity patterns

        Detects:
        - Multiple failed login attempts
        - Repeated rate limit violations
        - Unusual access patterns
        """

        # Define suspicious event types
        suspicious_events = [
            AuditEventType.LOGIN_FAILED,
            AuditEventType.RATE_LIMIT_EXCEEDED,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.INVALID_TOKEN,
        ]

        if event_type not in suspicious_events:
            return

        try:
            # Count recent suspicious events
            identifier = user_id or ip_address or "unknown"
            cache_key = f"suspicious:{event_type}:{identifier}"

            # Increment counter
            current_count = await redis_service.redis_client.incr(cache_key)
            await redis_service.redis_client.expire(cache_key, 3600)  # 1 hour window

            # Threshold for alerting
            threshold = 5

            if current_count >= threshold:
                # Log critical alert
                logger.critical(
                    f"Suspicious activity detected: {event_type}",
                    event_type=event_type,
                    identifier=identifier,
                    count=current_count,
                    window="1 hour"
                )

                # TODO: Send alert (email, Slack, etc.)
                # await send_security_alert(event_type, identifier, current_count)

        except Exception as e:
            logger.error(f"Failed to check suspicious activity: {e}")

    # Convenience methods for common events

    @staticmethod
    async def log_login_success(user_id: str, ip_address: str, db: Optional[AsyncSession] = None):
        """Log successful login"""
        await AuditService.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            severity="info",
            db=db
        )

    @staticmethod
    async def log_login_failed(email: str, ip_address: str, reason: str, db: Optional[AsyncSession] = None):
        """Log failed login attempt"""
        await AuditService.log_event(
            event_type=AuditEventType.LOGIN_FAILED,
            ip_address=ip_address,
            details={"email": email, "reason": reason},
            severity="warning",
            db=db
        )

    @staticmethod
    async def log_permission_denied(user_id: str, resource: str, required_permission: str):
        """Log permission denied"""
        await AuditService.log_event(
            event_type=AuditEventType.PERMISSION_DENIED,
            user_id=user_id,
            details={"resource": resource, "required_permission": required_permission},
            severity="warning"
        )

    @staticmethod
    async def log_rate_limit_exceeded(user_id: Optional[str], ip_address: str, resource: str):
        """Log rate limit exceeded"""
        await AuditService.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id=user_id,
            ip_address=ip_address,
            details={"resource": resource},
            severity="warning"
        )


# Global audit service instance
audit_service = AuditService()
