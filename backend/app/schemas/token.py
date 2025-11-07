from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenMeta(BaseModel):
    id: UUID
    expires_at: datetime
    revoked: bool


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRevokeRequest(BaseModel):
    refresh_token: str
