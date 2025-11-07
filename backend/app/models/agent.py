import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class AgentFramework(enum.Enum):
    crewai = "crewai"
    langchain = "langchain"
    openai = "openai"


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    framework = Column(Enum(AgentFramework), nullable=False)
    description = Column(String(500), nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = relationship("User", back_populates="agents")
    experiments = relationship("Experiment", back_populates="agent", cascade="all, delete-orphan")
