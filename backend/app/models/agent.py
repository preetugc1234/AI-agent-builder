"""
Agent database models
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.db.database import Base


class AgentStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    DEPLOYED = "deployed"
    ERROR = "error"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    vibe_prompt = Column(Text, nullable=False)

    # Generated content
    architecture = Column(Text, nullable=True)  # Agent 1 output
    generated_code = Column(Text, nullable=True)  # Agent 2 output
    review_notes = Column(Text, nullable=True)  # Agent 3 output
    final_code = Column(Text, nullable=True)  # Final reviewed code

    # Metadata
    file_structure = Column(JSON, default=list)
    integrations = Column(JSON, default=list)
    status = Column(String(50), default=AgentStatus.DRAFT.value)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "vibe_prompt": self.vibe_prompt,
            "architecture": self.architecture,
            "generated_code": self.generated_code,
            "review_notes": self.review_notes,
            "final_code": self.final_code,
            "file_structure": self.file_structure,
            "integrations": self.integrations,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
