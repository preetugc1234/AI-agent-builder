"""
Agent Execution API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.models import User, Agent, ExecutionLog
from app.schemas.schemas import ExecutionRequest, ExecutionResponse
from app.api.auth import get_current_user
from app.workflows.agent_execution import AgentExecutionWorkflow

router = APIRouter()


@router.post("/start")
async def start_execution(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start agent execution
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

    # Create execution log
    execution_log = ExecutionLog(
        agent_id=agent.id,
        execution_type="production",
        status="running",
        input_data=request.input_data
    )

    db.add(execution_log)
    await db.commit()
    await db.refresh(execution_log)

    # Start execution in background (WebSocket handles real-time updates)
    async def run_execution():
        workflow = AgentExecutionWorkflow(str(agent.id))
        try:
            result = await workflow.execute_agent_with_websocket(request.input_data)

            # Update execution log
            async with AsyncSession(db.bind) as session:
                log = await session.get(ExecutionLog, execution_log.id)
                log.status = "completed"
                log.output_data = result
                await session.commit()

        except Exception as e:
            # Update execution log with error
            async with AsyncSession(db.bind) as session:
                log = await session.get(ExecutionLog, execution_log.id)
                log.status = "failed"
                log.error_message = str(e)
                await session.commit()

    background_tasks.add_task(run_execution)

    return {
        "status": "started",
        "execution_id": str(execution_log.id),
        "agent_id": str(agent.id),
        "message": "Agent execution started successfully"
    }


@router.get("/history/{agent_id}", response_model=List[ExecutionResponse])
async def get_execution_history(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get execution history for an agent
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

    # Get execution logs
    result = await db.execute(
        select(ExecutionLog).where(
            ExecutionLog.agent_id == agent_id
        ).order_by(ExecutionLog.created_at.desc())
    )
    executions = result.scalars().all()

    return executions


@router.get("/status/{execution_id}", response_model=ExecutionResponse)
async def get_execution_status(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get execution status
    """
    result = await db.execute(
        select(ExecutionLog).where(ExecutionLog.id == execution_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    # Verify agent belongs to user
    result = await db.execute(
        select(Agent).where(
            Agent.id == execution.agent_id,
            Agent.user_id == current_user.id
        )
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return execution
