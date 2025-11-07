from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.experiment import ExperimentStatus


class ExperimentBase(BaseModel):
    name: str = Field(..., max_length=150)
    agent_id: Optional[UUID] = None
    input_payload: Dict[str, Any] = Field(default_factory=dict)


class ExperimentCreate(ExperimentBase):
    pass


class ExperimentRead(ExperimentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ExperimentStatus
    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ExperimentStatusResponse(BaseModel):
    id: UUID
    status: ExperimentStatus
    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
