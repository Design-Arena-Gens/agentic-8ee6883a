from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., max_length=100)
    email: EmailStr
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdatePreferences(BaseModel):
    preferences: Dict[str, Any]
