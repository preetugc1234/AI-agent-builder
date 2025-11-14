"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============= User Schemas =============
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    subscription_tier: str
    subscription_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Agent Schemas =============
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    vibe_prompt: str = Field(..., min_length=10)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    vibe_prompt: Optional[str] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    vibe_prompt: str
    generated_code: Optional[str]
    docker_image_url: Optional[str]
    status: str
    integrations: List[str]
    flow_data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= Integration Schemas =============
class IntegrationConnect(BaseModel):
    service: str
    credentials: Optional[Dict[str, str]] = None
    redirect_uri: Optional[str] = None


class IntegrationResponse(BaseModel):
    id: UUID
    service_name: str
    auth_type: str
    is_active: bool
    last_used: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Execution Schemas =============
class ExecutionRequest(BaseModel):
    agent_id: UUID
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    id: UUID
    agent_id: UUID
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    duration_seconds: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= Deployment Schemas =============
class DeploymentRequest(BaseModel):
    agent_id: UUID
    platform: str = "ecs"  # ecs, lambda, local


class DeploymentResponse(BaseModel):
    id: UUID
    agent_id: UUID
    platform: str
    status: str
    deployment_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= AI Generation Schemas =============
class AIGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    integrations: List[str] = Field(default_factory=list)


class AIGenerationResponse(BaseModel):
    code: str
    files: Dict[str, str]
    integrations: List[str]
    flow_data: Dict[str, Any]


# ============= WebSocket Message Schemas =============
class WSMessage(BaseModel):
    type: str
    agent_id: Optional[UUID] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


# ============= Subscription Schemas =============
class SubscriptionPlanResponse(BaseModel):
    id: UUID
    name: str
    price_monthly: Optional[float]
    price_yearly: Optional[float]
    max_agents: int
    max_deployments: int
    features: Dict[str, Any]

    class Config:
        from_attributes = True
