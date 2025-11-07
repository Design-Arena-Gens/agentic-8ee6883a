import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ExperimentStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_configs.id", ondelete="SET NULL"))
    name = Column(String(150), nullable=False)
    status = Column(Enum(ExperimentStatus), nullable=False, default=ExperimentStatus.pending)
    input_payload = Column(JSON, nullable=False, default=dict)
    result_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="experiments")
    agent = relationship("AgentConfig", back_populates="experiments")
