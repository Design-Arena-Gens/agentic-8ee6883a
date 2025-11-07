from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models import User
from app.schemas import UserRead, UserUpdatePreferences

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_active_user)) -> UserRead:
    return current_user


@router.patch("/me/preferences", response_model=UserRead)
async def update_preferences(
    payload: UserUpdatePreferences,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    current_user.preferences = payload.preferences
    await db.commit()
    await db.refresh(current_user)
    return current_user

