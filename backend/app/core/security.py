from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models import RefreshToken, User

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        jti = payload.get("jti")
        if jti is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_valid_refresh_token(jti: str, db: AsyncSession) -> RefreshToken:
    stmt = select(RefreshToken).where(RefreshToken.jti == jti)
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    if (
        token is None
        or token.revoked
        or token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired",
        )
    return token

