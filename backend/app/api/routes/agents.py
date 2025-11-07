from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models import AgentConfig, User
from app.schemas import AgentCreate, AgentRead, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


async def _get_agent_or_404(
    agent_id: UUID, user: User, db: AsyncSession
) -> AgentConfig:
    stmt = select(AgentConfig).where(AgentConfig.id == agent_id, AgentConfig.user_id == user.id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.get("/", response_model=list[AgentRead])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AgentRead]:
    stmt = select(AgentConfig).where(AgentConfig.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AgentRead:
    agent = AgentConfig(
        user_id=current_user.id,
        name=payload.name,
        framework=payload.framework,
        description=payload.description,
        parameters=payload.parameters,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AgentRead:
    agent = await _get_agent_or_404(agent_id, current_user, db)
    return agent


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AgentRead:
    agent = await _get_agent_or_404(agent_id, current_user, db)
    if payload.name is not None:
        agent.name = payload.name
    if payload.framework is not None:
        agent.framework = payload.framework
    if payload.description is not None:
        agent.description = payload.description
    if payload.parameters is not None:
        agent.parameters = payload.parameters
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    agent = await _get_agent_or_404(agent_id, current_user, db)
    await db.delete(agent)
    await db.commit()

