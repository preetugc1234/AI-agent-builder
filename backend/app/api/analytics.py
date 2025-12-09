"""
Analytics API routes
Provides user statistics and metrics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import User, Agent, ExecutionLog
from app.api.auth import get_current_user

router = APIRouter()


class AnalyticsResponse(BaseModel):
    total_agents: int
    time_saved_hours: float
    overall_success_rate: float
    total_executions: int


@router.get("/", response_model=AnalyticsResponse)
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for the current user
    """
    # Count total agents
    total_agents_query = await db.execute(
        select(func.count(Agent.id)).where(Agent.user_id == current_user.id)
    )
    total_agents = total_agents_query.scalar() or 0

    # Count total executions
    total_executions_query = await db.execute(
        select(func.count(ExecutionLog.id))
        .join(Agent)
        .where(Agent.user_id == current_user.id)
    )
    total_executions = total_executions_query.scalar() or 0

    # Count successful executions
    successful_executions_query = await db.execute(
        select(func.count(ExecutionLog.id))
        .join(Agent)
        .where(Agent.user_id == current_user.id, ExecutionLog.status == 'success')
    )
    successful_executions = successful_executions_query.scalar() or 0

    # Calculate success rate
    overall_success_rate = (
        (successful_executions / total_executions * 100)
        if total_executions > 0
        else 0.0
    )

    # Calculate time saved (estimate: 2 hours per agent created + 0.5 hours per successful execution)
    time_saved_hours = (total_agents * 2.0) + (successful_executions * 0.5)

    return AnalyticsResponse(
        total_agents=total_agents,
        time_saved_hours=round(time_saved_hours, 1),
        overall_success_rate=round(overall_success_rate, 1),
        total_executions=total_executions
    )
