import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import require_valid_refresh_token
from app.db.session import get_db
from app.models import User
from app.schemas import (
    TokenPair,
    TokenRefreshRequest,
    TokenRevokeRequest,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    existing = await AuthService.get_user_by_email(db, email=payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=AuthService.hash_password(payload.password),
        preferences=payload.preferences,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
async def login_user(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    user = await AuthService.get_user_by_email(db, email=payload.email)
    if not user or not AuthService.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    jti = uuid.uuid4().hex
    access_token = AuthService.create_access_token(subject=str(user.id), jti=jti)
    refresh_token = AuthService.create_refresh_token(subject=str(user.id), jti=jti)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.refresh_token_expire_minutes
    )

    token_record = await AuthService.persist_refresh_token(
        db,
        user_id=user.id,
        jti=jti,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    response.headers["X-Refresh-Token-Id"] = str(token_record.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(payload: TokenRefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    decoded = await AuthService.decode_refresh_token(payload.refresh_token)
    token = await require_valid_refresh_token(decoded["jti"], db)

    new_jti = uuid.uuid4().hex
    access_token = AuthService.create_access_token(subject=decoded["sub"], jti=new_jti)
    refresh_token = AuthService.create_refresh_token(subject=decoded["sub"], jti=new_jti)

    token.jti = new_jti
    token.expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    token.revoked = False
    token.revoked_at = None
    await db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(payload: TokenRevokeRequest, db: AsyncSession = Depends(get_db)) -> Response:
    decoded = await AuthService.decode_refresh_token(payload.refresh_token)
    await AuthService.revoke_refresh_token(db, jti=decoded["jti"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)
