from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.agent import AgentFramework


class AgentBase(BaseModel):
    name: str = Field(..., max_length=150)
    framework: AgentFramework
    description: Optional[str] = Field(default=None, max_length=500)
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("framework")
    @classmethod
    def normalize_framework(cls, value: str | AgentFramework) -> AgentFramework:
        if isinstance(value, AgentFramework):
            return value
        try:
            return AgentFramework(value.lower())
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("Unsupported agent framework") from exc


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=150)
    framework: Optional[AgentFramework] = None
    description: Optional[str] = Field(default=None, max_length=500)
    parameters: Optional[Dict[str, Any]] = None

    @field_validator("framework")
    @classmethod
    def normalize_framework(cls, value: Optional[str | AgentFramework]) -> Optional[AgentFramework]:
        if value is None:
            return value
        if isinstance(value, AgentFramework):
            return value
        try:
            return AgentFramework(value.lower())
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("Unsupported agent framework") from exc


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
