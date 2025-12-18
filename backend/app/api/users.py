"""
User Profile API Routes
Enhanced with structured logging, usage statistics, and GDPR compliance
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import User, Agent, TokenUsage, UserIntegration, Deployment
from app.api.auth import get_current_user
from app.core.logging_config import get_logger
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError
)
from app.services.audit_service import audit_service
from app.services.redis_service import redis_service
from app.services.quota_service import get_quota_service, QuotaType

logger = get_logger(__name__)
router = APIRouter()


# ============================
# Request/Response Models
# ============================

class UserProfileUpdate(BaseModel):
    """User profile update request"""
    email: Optional[str] = None


class UserStatsResponse(BaseModel):
    """User usage statistics response"""
    user_id: str
    email: str
    subscription_tier: str
    subscription_status: str
    member_since: str

    # Agent statistics
    total_agents: int
    agents_by_status: dict

    # Token usage statistics
    tokens_today: int
    tokens_this_month: int
    tokens_total: int

    # Deployment statistics
    total_deployments: int
    active_deployments: int

    # Integration statistics
    total_integrations: int
    active_integrations: int

    # Quota information
    quota_limits: dict
    quota_usage: dict


# ============================
# Endpoints
# ============================

@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user usage statistics and quotas

    **Statistics Included**:
    - Agent counts (total, by status)
    - Token usage (today, this month, total)
    - Deployment counts (total, active)
    - Integration counts (total, active)
    - Quota limits and current usage

    **Caching**: Results cached for 5 minutes
    """
    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id)
    )

    request_logger.info("Get user stats request received")

    # Try to get from cache first
    cache_key = f"user:{current_user.id}:stats"
    cached_stats = await redis_service.cache_get(cache_key)

    if cached_stats:
        request_logger.info("User stats fetched from cache")
        return cached_stats

    # Fetch agent statistics
    agent_count_result = await db.execute(
        select(func.count(Agent.id)).where(Agent.user_id == current_user.id)
    )
    total_agents = agent_count_result.scalar() or 0

    # Fetch agents by status
    agents_by_status_result = await db.execute(
        select(Agent.status, func.count(Agent.id))
        .where(Agent.user_id == current_user.id)
        .group_by(Agent.status)
    )
    agents_by_status = {status: count for status, count in agents_by_status_result.all()}

    # Fetch token usage statistics
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Tokens today
    tokens_today_result = await db.execute(
        select(func.sum(TokenUsage.total_tokens))
        .where(
            and_(
                TokenUsage.user_id == current_user.id,
                TokenUsage.created_at >= today_start
            )
        )
    )
    tokens_today = tokens_today_result.scalar() or 0

    # Tokens this month
    tokens_month_result = await db.execute(
        select(func.sum(TokenUsage.total_tokens))
        .where(
            and_(
                TokenUsage.user_id == current_user.id,
                TokenUsage.created_at >= month_start
            )
        )
    )
    tokens_this_month = tokens_month_result.scalar() or 0

    # Total tokens
    tokens_total_result = await db.execute(
        select(func.sum(TokenUsage.total_tokens))
        .where(TokenUsage.user_id == current_user.id)
    )
    tokens_total = tokens_total_result.scalar() or 0

    # Fetch deployment statistics
    deployment_count_result = await db.execute(
        select(func.count(Deployment.id))
        .join(Agent)
        .where(Agent.user_id == current_user.id)
    )
    total_deployments = deployment_count_result.scalar() or 0

    active_deployments_result = await db.execute(
        select(func.count(Deployment.id))
        .join(Agent)
        .where(
            and_(
                Agent.user_id == current_user.id,
                Deployment.status == "running"
            )
        )
    )
    active_deployments = active_deployments_result.scalar() or 0

    # Fetch integration statistics
    integration_count_result = await db.execute(
        select(func.count(UserIntegration.id))
        .where(UserIntegration.user_id == current_user.id)
    )
    total_integrations = integration_count_result.scalar() or 0

    active_integrations_result = await db.execute(
        select(func.count(UserIntegration.id))
        .where(
            and_(
                UserIntegration.user_id == current_user.id,
                UserIntegration.is_active == True
            )
        )
    )
    active_integrations = active_integrations_result.scalar() or 0

    # Define quota limits based on tier
    quota_limits = {
        "free": {
            "max_agents": 10,
            "max_deployments": 2,
            "max_ai_tokens_per_day": 50000,
            "max_integrations": 3
        },
        "pro": {
            "max_agents": -1,  # unlimited
            "max_deployments": 10,
            "max_ai_tokens_per_day": 500000,
            "max_integrations": 10
        },
        "enterprise": {
            "max_agents": -1,  # unlimited
            "max_deployments": -1,  # unlimited
            "max_ai_tokens_per_day": -1,  # unlimited
            "max_integrations": -1  # unlimited
        }
    }

    tier_limits = quota_limits.get(current_user.subscription_tier, quota_limits["free"])

    # Calculate quota usage percentages
    quota_usage = {
        "agents": {
            "current": total_agents,
            "limit": tier_limits["max_agents"],
            "percentage": (total_agents / tier_limits["max_agents"] * 100) if tier_limits["max_agents"] > 0 else 0
        },
        "deployments": {
            "current": active_deployments,
            "limit": tier_limits["max_deployments"],
            "percentage": (active_deployments / tier_limits["max_deployments"] * 100) if tier_limits["max_deployments"] > 0 else 0
        },
        "tokens_today": {
            "current": tokens_today,
            "limit": tier_limits["max_ai_tokens_per_day"],
            "percentage": (tokens_today / tier_limits["max_ai_tokens_per_day"] * 100) if tier_limits["max_ai_tokens_per_day"] > 0 else 0
        },
        "integrations": {
            "current": active_integrations,
            "limit": tier_limits["max_integrations"],
            "percentage": (active_integrations / tier_limits["max_integrations"] * 100) if tier_limits["max_integrations"] > 0 else 0
        }
    }

    # Build response
    stats = {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "subscription_tier": current_user.subscription_tier,
        "subscription_status": current_user.subscription_status,
        "member_since": current_user.created_at.isoformat() if current_user.created_at else None,
        "total_agents": total_agents,
        "agents_by_status": agents_by_status,
        "tokens_today": tokens_today,
        "tokens_this_month": tokens_this_month,
        "tokens_total": tokens_total,
        "total_deployments": total_deployments,
        "active_deployments": active_deployments,
        "total_integrations": total_integrations,
        "active_integrations": active_integrations,
        "quota_limits": tier_limits,
        "quota_usage": quota_usage
    }

    request_logger.info(
        "User stats fetched successfully",
        total_agents=total_agents,
        tokens_today=tokens_today
    )

    # Cache for 5 minutes (300 seconds)
    await redis_service.cache_set(
        cache_key,
        stats,
        expire_seconds=300
    )

    return stats


@router.put("/me")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile

    **Updatable Fields**:
    - email: Email address (must be unique)

    **Note**: Password changes should be done through /api/auth/change-password endpoint

    **Cache**: Invalidates user session cache on update
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        ip_address=client_ip
    )

    request_logger.info("User profile update request received")

    # Track what fields are being updated
    updated_fields = []

    # Update email if provided
    if profile_data.email is not None:
        # Validate email format
        if "@" not in profile_data.email or "." not in profile_data.email:
            raise ValidationError("Invalid email format", field="email")

        # Check if email is already taken by another user
        result = await db.execute(
            select(User).where(
                and_(
                    User.email == profile_data.email,
                    User.id != current_user.id
                )
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            request_logger.warning(
                "Profile update failed: Email already in use",
                email=profile_data.email
            )
            raise ValidationError(
                "Email address is already in use",
                field="email"
            )

        current_user.email = profile_data.email
        updated_fields.append("email")

    if not updated_fields:
        request_logger.info("No fields to update")
        return {
            "message": "No changes made",
            "user": {
                "id": str(current_user.id),
                "email": current_user.email,
                "subscription_tier": current_user.subscription_tier,
                "subscription_status": current_user.subscription_status
            }
        }

    try:
        await db.commit()
        await db.refresh(current_user)

        request_logger.info(
            "User profile updated successfully",
            updated_fields=updated_fields
        )

        # Invalidate session cache (will be updated on next request)
        session_key = f"session:{current_user.id}"
        await redis_service.delete_session(str(current_user.id))

        # Also invalidate stats cache
        stats_cache_key = f"user:{current_user.id}:stats"
        await redis_service.cache_delete(stats_cache_key)

        # Log profile update audit event
        await audit_service.log_event(
            event_type="profile_updated",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "updated_fields": updated_fields,
                "new_email": current_user.email if "email" in updated_fields else None
            },
            severity="info",
            db=db
        )

        return {
            "message": "Profile updated successfully",
            "updated_fields": updated_fields,
            "user": {
                "id": str(current_user.id),
                "email": current_user.email,
                "subscription_tier": current_user.subscription_tier,
                "subscription_status": current_user.subscription_status,
                "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
            }
        }

    except Exception as e:
        await db.rollback()
        request_logger.exception("Profile update failed with database error")
        raise


@router.delete("/me")
async def delete_user_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user account and all associated data (GDPR compliance)

    **Warning**: This action is irreversible!

    **Deleted Data**:
    - User profile
    - All agents
    - All deployments
    - All integrations
    - All token usage records
    - All execution logs
    - Redis sessions and cache
    - R2 uploaded files (if applicable)

    **GDPR Compliance**: Right to erasure (Article 17)
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        ip_address=client_ip,
        email=current_user.email
    )

    request_logger.warning("Account deletion request received")

    # Store user info for audit log before deletion
    user_email = current_user.email
    user_id = str(current_user.id)

    try:
        # Count resources before deletion for logging
        agent_count_result = await db.execute(
            select(func.count(Agent.id)).where(Agent.user_id == current_user.id)
        )
        total_agents = agent_count_result.scalar() or 0

        integration_count_result = await db.execute(
            select(func.count(UserIntegration.id)).where(UserIntegration.user_id == current_user.id)
        )
        total_integrations = integration_count_result.scalar() or 0

        # Delete user (cascade will delete agents, integrations, token_usage)
        await db.delete(current_user)
        await db.commit()

        request_logger.warning(
            "User account deleted successfully",
            total_agents_deleted=total_agents,
            total_integrations_deleted=total_integrations
        )

        # Delete from Redis
        await redis_service.delete_session(user_id)

        # Delete all user-related cache keys
        stats_cache_key = f"user:{user_id}:stats"
        await redis_service.cache_delete(stats_cache_key)

        agents_list_cache_key = f"user:{user_id}:agents:list"
        await redis_service.cache_delete(agents_list_cache_key)

        # Log account deletion audit event (without db parameter since user is deleted)
        await audit_service.log_event(
            event_type="account_deleted",
            user_id=user_id,
            ip_address=client_ip,
            details={
                "email": user_email,
                "agents_deleted": total_agents,
                "integrations_deleted": total_integrations,
                "gdpr_compliance": True
            },
            severity="warning"
        )

        return {
            "message": "Account deleted successfully",
            "user_id": user_id,
            "email": user_email,
            "resources_deleted": {
                "agents": total_agents,
                "integrations": total_integrations
            }
        }

    except Exception as e:
        await db.rollback()
        request_logger.exception("Account deletion failed with database error")
        raise


@router.get("/me/quotas")
async def get_user_quotas(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time quota usage for the current user

    **Quota Types**:
    - agents:total - Total agents allowed
    - agents:create_hour - Agent creations per hour
    - agents:create_day - Agent creations per day
    - executions:hour - Executions per hour
    - executions:day - Executions per day
    - ai_tokens:day - AI tokens per day
    - storage:mb - Storage in MB
    - websocket:concurrent - Concurrent WebSocket connections

    **Response Includes**:
    - Current usage for each quota type
    - Limits based on subscription tier
    - Percentage usage
    - Warnings for quotas > 80%
    - Blocked quotas at 100%
    """
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id)
    )

    request_logger.info("Get user quotas request received")

    # Get quota service
    quota_service = get_quota_service()

    if not quota_service:
        return {
            "status": "unavailable",
            "message": "Quota service not available",
            "tier": current_user.subscription_tier,
            "quotas": {}
        }

    # Get usage summary
    summary = await quota_service.get_usage_summary(
        user_id=str(current_user.id),
        tier=current_user.subscription_tier
    )

    request_logger.info(
        "User quotas fetched successfully",
        warnings=len(summary.get("warnings", [])),
        blocked=len(summary.get("blocked", []))
    )

    return {
        "status": "ok",
        "user_id": str(current_user.id),
        "tier": current_user.subscription_tier,
        "quotas": summary["quotas"],
        "warnings": summary["warnings"],
        "blocked": summary["blocked"],
        "upgrade_url": "/pricing" if summary["blocked"] or summary["warnings"] else None
    }


@router.post("/me/quotas/reset/{quota_type}")
async def reset_user_quota(
    quota_type: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Reset a specific quota (admin only or for testing)

    **Note**: This endpoint is only available for users with admin privileges
    or during testing. In production, quotas reset automatically based on
    their TTL (hourly, daily, etc.)
    """
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id)
    )

    # Only allow for enterprise users (for testing) or admins
    if current_user.subscription_tier not in ["enterprise", "admin"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="Only enterprise users can manually reset quotas"
        )

    quota_service = get_quota_service()

    if not quota_service:
        return {"status": "error", "message": "Quota service not available"}

    # Reset the quota
    success = await quota_service.reset_quota(
        user_id=str(current_user.id),
        quota_type=quota_type
    )

    if success:
        request_logger.info(f"Quota {quota_type} reset successfully")
        return {
            "status": "ok",
            "message": f"Quota {quota_type} reset successfully",
            "quota_type": quota_type
        }
    else:
        return {
            "status": "error",
            "message": f"Failed to reset quota {quota_type}"
        }
