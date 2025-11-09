"""
Deployments API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.models import User, Agent, Deployment
from app.schemas.schemas import DeploymentRequest, DeploymentResponse
from app.api.auth import get_current_user
from app.workflows.deployment import DeploymentWorkflow

router = APIRouter()


@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy an agent
    """
    # Verify agent belongs to user
    result = await db.execute(
        select(Agent).where(
            Agent.id == request.agent_id,
            Agent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Create deployment record
    deployment = Deployment(
        agent_id=agent.id,
        platform=request.platform,
        status="pending"
    )

    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)

    # Start deployment in background (WebSocket handles real-time updates)
    async def run_deployment():
        workflow = DeploymentWorkflow(str(agent.id))
        try:
            result = await workflow.deploy_agent_with_websocket(request.platform)

            # Update deployment record
            async with AsyncSession(db.bind) as session:
                dep = await session.get(Deployment, deployment.id)
                dep.status = "running"
                dep.deployment_url = result.get("url")
                await session.commit()

        except Exception as e:
            # Update deployment record with error
            async with AsyncSession(db.bind) as session:
                dep = await session.get(Deployment, deployment.id)
                dep.status = "error"
                dep.error_message = str(e)
                await session.commit()

    background_tasks.add_task(run_deployment)

    return deployment


@router.get("/agent/{agent_id}", response_model=List[DeploymentResponse])
async def get_agent_deployments(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all deployments for an agent
    """
    # Verify agent belongs to user
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Get deployments
    result = await db.execute(
        select(Deployment).where(
            Deployment.agent_id == agent_id
        ).order_by(Deployment.created_at.desc())
    )
    deployments = result.scalars().all()

    return deployments


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific deployment
    """
    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )

    # Verify agent belongs to user
    result = await db.execute(
        select(Agent).where(
            Agent.id == deployment.agent_id,
            Agent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return deployment


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def stop_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stop a deployment
    """
    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )

    # Verify agent belongs to user
    result = await db.execute(
        select(Agent).where(
            Agent.id == deployment.agent_id,
            Agent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Update deployment status
    deployment.status = "stopped"
    await db.commit()

    # TODO: Actually stop the ECS task/Lambda function

    return None
