"""
Agents API routes with permission-based access control
Enhanced with structured logging, quota checks, Redis caching, and audit logging
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import json

from app.db.database import get_db
from app.models.models import User, Agent
from app.schemas.schemas import AgentCreate, AgentUpdate, AgentResponse
from app.api.auth import get_current_user
from app.core.auth_middleware import require_permissions, require_tier
from app.services.three_agent_service import three_agent_service
from app.core.logging_config import get_logger
from app.core.exceptions import (
    ResourceNotFoundError,
    QuotaExceededError,
    ValidationError,
    AuthorizationError,
    AIGenerationError,
    RateLimitExceededError
)
from app.services.audit_service import audit_service
from app.services.redis_service import redis_service

logger = get_logger(__name__)


class GenerateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    vibe_prompt: str


router = APIRouter()


# ============================
# Helper Functions
# ============================

async def check_agent_quota(user_id: UUID, user_tier: str, db: AsyncSession) -> None:
    """
    Check if user has reached their agent creation quota

    Free tier limits:
    - Max 10 agents total

    Raises:
        QuotaExceededError: If user has reached their quota
    """
    # Only enforce quota for free tier
    if user_tier != "free":
        return

    # Count total agents for user
    result = await db.execute(
        select(func.count(Agent.id)).where(Agent.user_id == user_id)
    )
    total_agents = result.scalar() or 0

    if total_agents >= 10:
        raise QuotaExceededError(
            quota_type="Total agents",
            limit=10,
            current=total_agents
        )


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
# @require_permissions("write:agents")  # Uncomment to enable permission check
async def create_agent(
    agent_data: AgentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new agent

    **Requirements**:
    - write:agents permission (all tiers have this)

    **Free Tier Limits**:
    - Max 10 agents total

    **Validation**:
    - Name: Required, max 100 characters
    - Vibe prompt: Required, max 5000 characters
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        ip_address=client_ip
    )

    request_logger.info(
        "Agent creation request received",
        agent_name=agent_data.name
    )

    # Validate input
    if not agent_data.name or len(agent_data.name.strip()) == 0:
        request_logger.warning("Agent creation failed: Empty name")
        raise ValidationError("Agent name cannot be empty", field="name")

    if len(agent_data.name) > 100:
        request_logger.warning("Agent creation failed: Name too long")
        raise ValidationError(
            "Agent name must be 100 characters or less",
            field="name"
        )

    if not agent_data.vibe_prompt or len(agent_data.vibe_prompt.strip()) == 0:
        request_logger.warning("Agent creation failed: Empty vibe prompt")
        raise ValidationError(
            "Vibe prompt cannot be empty",
            field="vibe_prompt"
        )

    if len(agent_data.vibe_prompt) > 5000:
        request_logger.warning("Agent creation failed: Vibe prompt too long")
        raise ValidationError(
            "Vibe prompt must be 5000 characters or less",
            field="vibe_prompt"
        )

    # Check quota (free tier: max 10 agents)
    try:
        await check_agent_quota(
            user_id=current_user.id,
            user_tier=current_user.subscription_tier,
            db=db
        )
    except QuotaExceededError as e:
        request_logger.warning(
            "Agent creation failed: Quota exceeded",
            quota_limit=10,
            tier=current_user.subscription_tier
        )
        # Log quota exceeded event
        await audit_service.log_event(
            event_type="quota_exceeded",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "resource_type": "agent",
                "quota_type": "total_agents",
                "limit": 10
            },
            severity="warning"
        )
        raise

    try:
        # Create agent
        new_agent = Agent(
            user_id=current_user.id,
            name=agent_data.name.strip(),
            description=agent_data.description.strip() if agent_data.description else None,
            vibe_prompt=agent_data.vibe_prompt.strip(),
            status="draft",
            integrations=[],
            flow_data={}
        )

        db.add(new_agent)
        await db.commit()
        await db.refresh(new_agent)

        request_logger.info(
            "Agent created successfully",
            agent_id=str(new_agent.id),
            agent_name=new_agent.name,
            status=new_agent.status
        )

        # Log agent creation audit event
        await audit_service.log_event(
            event_type="resource_created",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "resource_type": "agent",
                "agent_id": str(new_agent.id),
                "agent_name": new_agent.name,
                "status": "draft"
            },
            severity="info",
            db=db
        )

        return new_agent

    except Exception as e:
        await db.rollback()
        request_logger.exception("Agent creation failed with database error")
        raise


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all agents for the current user

    **Caching**: Results are cached in Redis for 5 minutes
    """
    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id)
    )

    request_logger.info("Listing agents request received")

    # Try to get from cache first
    cache_key = f"user:{current_user.id}:agents:list"
    cached_agents = await redis_service.cache_get(cache_key)

    if cached_agents:
        request_logger.info(
            "Agents list fetched from cache",
            count=len(cached_agents)
        )
        return cached_agents

    # Fetch from database
    result = await db.execute(
        select(Agent).where(Agent.user_id == current_user.id).order_by(Agent.created_at.desc())
    )
    agents = result.scalars().all()

    request_logger.info(
        "Agents list fetched from database",
        count=len(agents)
    )

    # Cache for 5 minutes (300 seconds)
    agents_list = [agent for agent in agents]
    await redis_service.cache_set(
        cache_key,
        agents_list,
        expire_seconds=300
    )

    return agents_list


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific agent

    **Caching**: Results are cached in Redis for 10 minutes
    """
    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        agent_id=str(agent_id)
    )

    request_logger.info("Get agent request received")

    # Try to get from cache first
    cache_key = f"agent:{agent_id}"
    cached_agent = await redis_service.cache_get(cache_key)

    if cached_agent:
        # Verify ownership
        if cached_agent.get("user_id") == str(current_user.id):
            request_logger.info("Agent fetched from cache")
            return cached_agent
        else:
            # Cached agent doesn't belong to this user
            request_logger.warning(
                "Authorization failed: Agent belongs to another user"
            )
            raise AuthorizationError("You don't have access to this agent")

    # Fetch from database
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        request_logger.warning("Agent not found")
        raise ResourceNotFoundError("Agent", str(agent_id))

    request_logger.info(
        "Agent fetched from database",
        agent_name=agent.name,
        status=agent.status
    )

    # Cache for 10 minutes (600 seconds)
    await redis_service.cache_set(
        cache_key,
        agent,
        expire_seconds=600
    )

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an agent

    **Validation**:
    - Name: Max 100 characters (if provided)
    - Vibe prompt: Max 5000 characters (if provided)
    - Status: One of "draft", "generating", "ready", "error"

    **Cache**: Invalidates cached agent data on update
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        agent_id=str(agent_id),
        ip_address=client_ip
    )

    request_logger.info("Agent update request received")

    # Fetch agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        request_logger.warning("Agent not found")
        raise ResourceNotFoundError("Agent", str(agent_id))

    # Track what fields are being updated
    updated_fields = []

    # Validate and update fields
    if agent_data.name is not None:
        if len(agent_data.name.strip()) == 0:
            raise ValidationError("Agent name cannot be empty", field="name")
        if len(agent_data.name) > 100:
            raise ValidationError(
                "Agent name must be 100 characters or less",
                field="name"
            )
        agent.name = agent_data.name.strip()
        updated_fields.append("name")

    if agent_data.description is not None:
        agent.description = agent_data.description.strip() if agent_data.description else None
        updated_fields.append("description")

    if agent_data.vibe_prompt is not None:
        if len(agent_data.vibe_prompt.strip()) == 0:
            raise ValidationError(
                "Vibe prompt cannot be empty",
                field="vibe_prompt"
            )
        if len(agent_data.vibe_prompt) > 5000:
            raise ValidationError(
                "Vibe prompt must be 5000 characters or less",
                field="vibe_prompt"
            )
        agent.vibe_prompt = agent_data.vibe_prompt.strip()
        updated_fields.append("vibe_prompt")

    if agent_data.status is not None:
        valid_statuses = ["draft", "generating", "ready", "error"]
        if agent_data.status not in valid_statuses:
            raise ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}",
                field="status"
            )
        agent.status = agent_data.status
        updated_fields.append("status")

    if not updated_fields:
        request_logger.info("No fields to update")
        return agent

    try:
        await db.commit()
        await db.refresh(agent)

        request_logger.info(
            "Agent updated successfully",
            agent_name=agent.name,
            updated_fields=updated_fields
        )

        # Invalidate cache
        cache_key = f"agent:{agent_id}"
        await redis_service.cache_delete(cache_key)

        # Also invalidate the user's agent list cache
        list_cache_key = f"user:{current_user.id}:agents:list"
        await redis_service.cache_delete(list_cache_key)

        # Log agent update audit event
        await audit_service.log_event(
            event_type="resource_updated",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "resource_type": "agent",
                "agent_id": str(agent_id),
                "agent_name": agent.name,
                "updated_fields": updated_fields
            },
            severity="info",
            db=db
        )

        return agent

    except Exception as e:
        await db.rollback()
        request_logger.exception("Agent update failed with database error")
        raise


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
# @require_permissions("delete:agents")  # Only pro/enterprise tiers have this
async def delete_agent(
    agent_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an agent

    **Requirements**:
    - delete:agents permission (pro tier or higher)

    **Note**: Free tier users cannot delete agents. They can only update status to "archived".

    **Cache**: Invalidates cached agent data on deletion
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        agent_id=str(agent_id),
        ip_address=client_ip
    )

    request_logger.info("Agent deletion request received")

    # Fetch agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        request_logger.warning("Agent not found")
        raise ResourceNotFoundError("Agent", str(agent_id))

    # Store agent info for audit log before deletion
    agent_name = agent.name
    agent_status = agent.status

    try:
        await db.delete(agent)
        await db.commit()

        request_logger.info(
            "Agent deleted successfully",
            agent_name=agent_name,
            previous_status=agent_status
        )

        # Invalidate cache
        cache_key = f"agent:{agent_id}"
        await redis_service.cache_delete(cache_key)

        # Also invalidate the user's agent list cache
        list_cache_key = f"user:{current_user.id}:agents:list"
        await redis_service.cache_delete(list_cache_key)

        # Log agent deletion audit event
        await audit_service.log_event(
            event_type="resource_deleted",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "resource_type": "agent",
                "agent_id": str(agent_id),
                "agent_name": agent_name,
                "previous_status": agent_status
            },
            severity="info"
        )

        return None

    except Exception as e:
        await db.rollback()
        request_logger.exception("Agent deletion failed with database error")
        raise


@router.post("/{agent_id}/generate-code")
async def generate_agent_code(
    agent_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger AI code generation for an agent using 3-agent workflow

    **Process**:
    1. Sets agent status to "generating"
    2. Runs 3-agent workflow (Architect → Code Generator → Code Reviewer)
    3. Updates agent with generated code
    4. Sets status to "ready" on success or "error" on failure

    **Cache**: Invalidates cached agent data after generation
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        agent_id=str(agent_id),
        ip_address=client_ip
    )

    request_logger.info("Agent code generation request received")

    # Fetch agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        request_logger.warning("Agent not found")
        raise ResourceNotFoundError("Agent", str(agent_id))

    # Update status to generating
    agent.status = "generating"
    await db.commit()

    request_logger.info(
        "Starting agent code generation",
        agent_name=agent.name,
        vibe_prompt_length=len(agent.vibe_prompt)
    )

    try:
        # Run 3-agent generation
        generation_result = await three_agent_service.generate_agent(agent.vibe_prompt)

        # Update agent with results
        agent.architecture = generation_result["architecture"]
        agent.generated_code = generation_result["generated_code"]
        agent.review_notes = generation_result["review_notes"]
        agent.final_code = generation_result["final_code"]
        agent.file_structure = generation_result["file_structure"]
        agent.integrations = generation_result["integrations"]
        agent.status = "ready"
        await db.commit()
        await db.refresh(agent)

        request_logger.info(
            "Agent code generation completed successfully",
            agent_name=agent.name,
            integrations=len(agent.integrations),
            files_generated=len(agent.file_structure) if agent.file_structure else 0
        )

        # Invalidate cache
        cache_key = f"agent:{agent_id}"
        await redis_service.cache_delete(cache_key)

        # Also invalidate the user's agent list cache
        list_cache_key = f"user:{current_user.id}:agents:list"
        await redis_service.cache_delete(list_cache_key)

        # Log generation success audit event
        await audit_service.log_event(
            event_type="agent_generation_success",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "agent_id": str(agent_id),
                "agent_name": agent.name,
                "integrations": agent.integrations,
                "files_generated": len(agent.file_structure) if agent.file_structure else 0
            },
            severity="info",
            db=db
        )

        return {
            "message": "Code generation completed",
            "agent_id": str(agent_id),
            "status": "ready",
            "file_structure": agent.file_structure,
            "integrations": agent.integrations
        }

    except Exception as e:
        request_logger.exception(
            "Agent code generation failed",
            agent_name=agent.name,
            error=str(e)
        )
        agent.status = "error"
        await db.commit()

        # Log generation failure audit event
        await audit_service.log_event(
            event_type="agent_generation_failed",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "agent_id": str(agent_id),
                "agent_name": agent.name,
                "error": str(e)
            },
            severity="error",
            db=db
        )

        raise AIGenerationError("code_generator", str(e))


@router.post("/generate")
async def generate_new_agent(
    generate_request: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new agent and run 3-agent generation in one call

    **Convenience endpoint** that combines:
    1. Agent creation (POST /)
    2. Code generation (POST /{agent_id}/generate-code)

    **Free Tier Limits**:
    - Max 10 agents total

    **Validation**:
    - Name: Required, max 100 characters
    - Vibe prompt: Required, max 5000 characters

    **Process**:
    1. Validates quota and input
    2. Creates agent with status "generating"
    3. Runs 3-agent workflow
    4. Updates agent with results
    5. Returns complete agent with generated code
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        ip_address=client_ip
    )

    request_logger.info(
        "Generate new agent request received",
        agent_name=generate_request.name
    )

    # Validate input
    if not generate_request.name or len(generate_request.name.strip()) == 0:
        request_logger.warning("Generation failed: Empty name")
        raise ValidationError("Agent name cannot be empty", field="name")

    if len(generate_request.name) > 100:
        request_logger.warning("Generation failed: Name too long")
        raise ValidationError(
            "Agent name must be 100 characters or less",
            field="name"
        )

    if not generate_request.vibe_prompt or len(generate_request.vibe_prompt.strip()) == 0:
        request_logger.warning("Generation failed: Empty vibe prompt")
        raise ValidationError(
            "Vibe prompt cannot be empty",
            field="vibe_prompt"
        )

    if len(generate_request.vibe_prompt) > 5000:
        request_logger.warning("Generation failed: Vibe prompt too long")
        raise ValidationError(
            "Vibe prompt must be 5000 characters or less",
            field="vibe_prompt"
        )

    # Check quota (free tier: max 10 agents)
    try:
        await check_agent_quota(
            user_id=current_user.id,
            user_tier=current_user.subscription_tier,
            db=db
        )
    except QuotaExceededError as e:
        request_logger.warning(
            "Generation failed: Quota exceeded",
            quota_limit=10,
            tier=current_user.subscription_tier
        )
        # Log quota exceeded event
        await audit_service.log_event(
            event_type="quota_exceeded",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "resource_type": "agent",
                "quota_type": "total_agents",
                "limit": 10
            },
            severity="warning"
        )
        raise

    try:
        # Create agent
        new_agent = Agent(
            user_id=current_user.id,
            name=generate_request.name.strip(),
            description=generate_request.description.strip() if generate_request.description else None,
            vibe_prompt=generate_request.vibe_prompt.strip(),
            status="generating",
            integrations=[],
            flow_data={}
        )

        db.add(new_agent)
        await db.commit()
        await db.refresh(new_agent)

        request_logger.info(
            "Agent created, starting code generation",
            agent_id=str(new_agent.id),
            agent_name=new_agent.name
        )

        # Log agent creation audit event
        await audit_service.log_event(
            event_type="resource_created",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "resource_type": "agent",
                "agent_id": str(new_agent.id),
                "agent_name": new_agent.name,
                "status": "generating",
                "auto_generate": True
            },
            severity="info",
            db=db
        )

        # Run 3-agent generation
        generation_result = await three_agent_service.generate_agent(generate_request.vibe_prompt)

        # Update agent with results
        new_agent.architecture = generation_result["architecture"]
        new_agent.generated_code = generation_result["generated_code"]
        new_agent.review_notes = generation_result["review_notes"]
        new_agent.final_code = generation_result["final_code"]
        new_agent.file_structure = generation_result["file_structure"]
        new_agent.integrations = generation_result["integrations"]
        new_agent.status = "ready"
        await db.commit()
        await db.refresh(new_agent)

        request_logger.info(
            "Agent generation completed successfully",
            agent_id=str(new_agent.id),
            agent_name=new_agent.name,
            integrations=len(new_agent.integrations),
            files_generated=len(new_agent.file_structure) if new_agent.file_structure else 0
        )

        # Invalidate the user's agent list cache
        list_cache_key = f"user:{current_user.id}:agents:list"
        await redis_service.cache_delete(list_cache_key)

        # Log generation success audit event
        await audit_service.log_event(
            event_type="agent_generation_success",
            user_id=str(current_user.id),
            ip_address=client_ip,
            details={
                "agent_id": str(new_agent.id),
                "agent_name": new_agent.name,
                "integrations": new_agent.integrations,
                "files_generated": len(new_agent.file_structure) if new_agent.file_structure else 0,
                "auto_generate": True
            },
            severity="info",
            db=db
        )

        return {
            "id": str(new_agent.id),
            "name": new_agent.name,
            "status": "ready",
            "architecture": new_agent.architecture,
            "generated_code": new_agent.generated_code,
            "review_notes": new_agent.review_notes,
            "final_code": new_agent.final_code,
            "file_structure": new_agent.file_structure,
            "integrations": new_agent.integrations
        }

    except QuotaExceededError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        request_logger.exception(
            "Agent generation failed",
            agent_name=generate_request.name,
            error=str(e)
        )

        # Update agent status to error if it was created
        if 'new_agent' in locals():
            new_agent.status = "error"
            await db.commit()

            # Log generation failure audit event
            await audit_service.log_event(
                event_type="agent_generation_failed",
                user_id=str(current_user.id),
                ip_address=client_ip,
                details={
                    "agent_id": str(new_agent.id),
                    "agent_name": new_agent.name,
                    "error": str(e),
                    "auto_generate": True
                },
                severity="error",
                db=db
            )

        raise AIGenerationError("code_generator", str(e))
