"""
Database models for VibeAgent Forge
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    cognito_id = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    subscription_tier = Column(String(50), default="free")
    subscription_status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("UserIntegration", back_populates="user", cascade="all, delete-orphan")


class Agent(Base):
    """Agent model"""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    vibe_prompt = Column(Text, nullable=False)
    # 3-Agent outputs
    architecture = Column(Text, nullable=True)  # Agent 1 output
    generated_code = Column(Text, nullable=True)  # Agent 2 output
    review_notes = Column(Text, nullable=True)  # Agent 3 output
    final_code = Column(Text, nullable=True)  # Final reviewed code
    file_structure = Column(JSON, default=list)  # Extracted file structure

    docker_image_url = Column(String(500), nullable=True)
    status = Column(String(50), default="draft")  # draft, generating, ready, deployed, error
    integrations = Column(JSON, default=list)
    flow_data = Column(JSON, default=dict)  # Store flow diagram data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="agents")
    deployments = relationship("Deployment", back_populates="agent", cascade="all, delete-orphan")


class UserIntegration(Base):
    """User integrations model"""
    __tablename__ = "user_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(100), nullable=False)  # gmail, slack, supabase, etc.
    auth_type = Column(String(50), nullable=False)  # oauth, api_key, aws_credentials
    encrypted_data = Column(Text, nullable=False)  # KMS encrypted credentials
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="integrations")


class Deployment(Base):
    """Deployment model"""
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), default="ecs")  # ecs, lambda, local
    ecs_task_arn = Column(String(500), nullable=True)
    status = Column(String(50), default="pending")  # pending, building, running, stopped, error
    logs_s3_url = Column(String(500), nullable=True)
    deployment_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="deployments")


class SubscriptionPlan(Base):
    """Subscription plans model"""
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    price_monthly = Column(DECIMAL(10, 2), nullable=True)
    price_yearly = Column(DECIMAL(10, 2), nullable=True)
    max_agents = Column(Integer, nullable=False)
    max_deployments = Column(Integer, nullable=False)
    features = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExecutionLog(Base):
    """Execution logs model"""
    __tablename__ = "execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    execution_type = Column(String(50), nullable=False)  # test, production
    status = Column(String(50), nullable=False)  # running, completed, failed
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
