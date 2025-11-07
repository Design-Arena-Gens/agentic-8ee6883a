import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import RefreshToken, User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
settings = get_settings()


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return pwd_context.verify(password, password_hash)

    @staticmethod
    def _create_token(
        *,
        subject: str,
        expires_delta: timedelta,
        secret_key: str,
        additional_claims: Optional[dict] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        to_encode = {"sub": subject, "exp": now + expires_delta, "iat": now}
        if additional_claims:
            to_encode.update(additional_claims)
        return jwt.encode(to_encode, secret_key, algorithm=settings.algorithm)

    @classmethod
    def create_access_token(cls, *, subject: str, jti: str) -> str:
        return cls._create_token(
            subject=subject,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
            secret_key=settings.secret_key,
            additional_claims={"jti": jti, "type": "access"},
        )

    @classmethod
    def create_refresh_token(cls, *, subject: str, jti: str) -> str:
        return cls._create_token(
            subject=subject,
            expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes),
            secret_key=settings.refresh_secret_key,
            additional_claims={"jti": jti, "type": "refresh"},
        )

    @staticmethod
    async def persist_refresh_token(
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        jti: str,
        expires_at: datetime,
        user_agent: Optional[str],
        ip_address: Optional[str],
    ) -> RefreshToken:
        token = RefreshToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, *, jti: str) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti, RefreshToken.revoked.is_(False))
            .values(revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, *, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_refresh_token(db: AsyncSession, *, jti: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def decode_refresh_token(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.refresh_secret_key,
                algorithms=[settings.algorithm],
                options={"require": ["exp", "iat", "sub", "jti"]},
            )
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )
            return payload
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate refresh token",
            ) from exc
