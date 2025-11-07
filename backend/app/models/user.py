import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    preferences = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    agents = relationship("AgentConfig", back_populates="owner", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="owner", cascade="all, delete-orphan")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
