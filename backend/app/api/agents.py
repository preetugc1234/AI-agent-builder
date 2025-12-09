"""
Agents API routes with permission-based access control
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import logging

from app.db.database import get_db
from app.models.models import User, Agent
from app.schemas.schemas import AgentCreate, AgentUpdate, AgentResponse
from app.api.auth import get_current_user
from app.core.auth_middleware import require_permissions, require_tier
from app.services.three_agent_service import three_agent_service

logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    vibe_prompt: str

router = APIRouter()


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
    Requires: write:agents permission
    """
    # Create agent
    new_agent = Agent(
        user_id=current_user.id,
        name=agent_data.name,
        description=agent_data.description,
        vibe_prompt=agent_data.vibe_prompt,
        status="draft",
        integrations=[],
        flow_data={}
    )

    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)

    return new_agent


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all agents for the current user
    """
    result = await db.execute(
        select(Agent).where(Agent.user_id == current_user.id).order_by(Agent.created_at.desc())
    )
    agents = result.scalars().all()

    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific agent
    """
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an agent
    """
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Update fields
    if agent_data.name is not None:
        agent.name = agent_data.name
    if agent_data.description is not None:
        agent.description = agent_data.description
    if agent_data.vibe_prompt is not None:
        agent.vibe_prompt = agent_data.vibe_prompt
    if agent_data.status is not None:
        agent.status = agent_data.status

    await db.commit()
    await db.refresh(agent)

    return agent


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
    Requires: delete:agents permission (pro tier or higher)
    """
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    await db.delete(agent)
    await db.commit()

    return None


@router.post("/{agent_id}/generate-code")
async def generate_agent_code(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger AI code generation for an agent using 3-agent workflow
    """
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Update status to generating
    agent.status = "generating"
    await db.commit()

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

        return {
            "message": "Code generation completed",
            "agent_id": str(agent_id),
            "status": "ready",
            "file_structure": agent.file_structure,
            "integrations": agent.integrations
        }

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        agent.status = "error"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate")
async def generate_new_agent(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new agent and run 3-agent generation in one call
    """
    # Create agent
    new_agent = Agent(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        vibe_prompt=request.vibe_prompt,
        status="generating",
        integrations=[],
        flow_data={}
    )

    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)

    try:
        # Run 3-agent generation
        generation_result = await three_agent_service.generate_agent(request.vibe_prompt)

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

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        new_agent.status = "error"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
