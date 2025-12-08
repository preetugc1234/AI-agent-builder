"""
Database models for NodeRush
Updated for new architecture with LangGraph 3-agent workflow
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class User(Base):
    """User model - Supabase Auth integration"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    cognito_id = Column(String(255), unique=True, nullable=True)  # Legacy field
    password_hash = Column(String(255), nullable=True)
    subscription_tier = Column(String(50), default="free", nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("UserIntegration", back_populates="user", cascade="all, delete-orphan")
    token_usage = relationship("TokenUsage", back_populates="user", cascade="all, delete-orphan")


class Agent(Base):
    """Agent model - LangGraph 3-agent workflow"""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    vibe_prompt = Column(Text, nullable=False)

    # 3-Agent LangGraph outputs
    architecture = Column(Text, nullable=True)          # Agent 1 (Architect) output
    generated_code = Column(Text, nullable=True)        # Agent 2 (Coder) output
    review_notes = Column(Text, nullable=True)          # Agent 3 (Reviewer) output
    final_code = Column(Text, nullable=True)            # Final reviewed code
    file_structure = Column(JSON, default=list)         # Extracted file structure

    # Deployment info
    docker_image_url = Column(String(500), nullable=True)
    status = Column(String(50), default="draft", nullable=False)  # draft, generating, ready, deployed, error
    integrations = Column(JSON, default=list)
    flow_data = Column(JSON, default=dict)  # Store flow diagram data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="agents")
    deployments = relationship("Deployment", back_populates="agent", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="agent", cascade="all, delete-orphan")


class UserIntegration(Base):
    """User integrations model - OAuth/API keys"""
    __tablename__ = "user_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False)  # gmail, slack, github, etc.
    auth_type = Column(String(50), nullable=False)      # oauth, api_key
    encrypted_data = Column(Text, nullable=False)       # Encrypted credentials
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="integrations")


class Deployment(Base):
    """Deployment model - Render/Vercel/Cloudflare"""
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), default="render", nullable=False)  # render, vercel, cloudflare
    task_arn = Column(String(500), nullable=True)  # Platform-specific ID
    status = Column(String(50), default="pending", nullable=False)  # pending, building, running, stopped, error
    logs_url = Column(String(500), nullable=True)
    deployment_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="deployments")


class SubscriptionPlan(Base):
    """Subscription plans model - Free tier limits"""
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    price_monthly = Column(DECIMAL(10, 2), nullable=True)
    price_yearly = Column(DECIMAL(10, 2), nullable=True)
    max_agents = Column(Integer, nullable=False)
    max_deployments = Column(Integer, nullable=False)
    max_executions_per_day = Column(Integer, nullable=False)
    max_ai_tokens_per_day = Column(Integer, nullable=False)
    max_storage_mb = Column(Integer, nullable=False)
    features = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExecutionLog(Base):
    """Execution logs model - LangGraph execution tracking"""
    __tablename__ = "execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_type = Column(String(50), nullable=False)  # test, production
    status = Column(String(50), nullable=False)          # running, completed, failed
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    tokens_used = Column(JSON, default=dict)  # {agent1: 1500, agent2: 2000, agent3: 1800}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="execution_logs")


class SecurityLog(Base):
    """Security logs model - Audit trail for security events"""
    __tablename__ = "security_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)  # failed_login, rate_limit_exceeded, etc.
    ip_address = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class TokenUsage(Base):
    """Token usage tracking model - AI token consumption"""
    __tablename__ = "token_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    agent_name = Column(String(50), nullable=False)  # agent1_architect, agent2_coder, agent3_reviewer
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    model = Column(String(100), nullable=False)  # nvidia/nemotron-nano-12b-v2-vl:free
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="token_usage")


class RateLimit(Base):
    """Rate limit tracking model - Track API rate limits"""
    __tablename__ = "rate_limits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    ip_address = Column(INET, nullable=True, index=True)
    resource = Column(String(100), nullable=False)  # agents:create, agents:execute, api:general
    request_count = Column(Integer, default=1)
    window_start = Column(DateTime(timezone=True), server_default=func.now())
    window_end = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
