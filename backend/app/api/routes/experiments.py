from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models import AgentConfig, Experiment, User
from app.schemas import ExperimentCreate, ExperimentRead, ExperimentStatusResponse
from app.services.agent_engine import AgentExecutionError, agent_engine

router = APIRouter(prefix="/experiments", tags=["experiments"])


async def _get_experiment_or_404(
    experiment_id: UUID, user: User, db: AsyncSession
) -> Experiment:
    stmt = select(Experiment).where(Experiment.id == experiment_id, Experiment.user_id == user.id)
    result = await db.execute(stmt)
    experiment = result.scalar_one_or_none()
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiment


@router.get("/", response_model=list[ExperimentRead])
async def list_experiments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ExperimentRead]:
    stmt = select(Experiment).where(Experiment.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    payload: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExperimentRead:
    agent: AgentConfig | None = None
    if payload.agent_id:
        stmt = select(AgentConfig).where(
            AgentConfig.id == payload.agent_id, AgentConfig.user_id == current_user.id
        )
        result = await db.execute(stmt)
        agent = result.scalar_one_or_none()
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    experiment = Experiment(
        user_id=current_user.id,
        agent_id=agent.id if agent else None,
        name=payload.name,
        input_payload=payload.input_payload,
    )
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)

    if agent:
        try:
            await agent_engine.run(experiment, agent)
        except AgentExecutionError as exc:
            experiment.error_message = str(exc)
            await db.commit()
            await db.refresh(experiment)
            raise HTTPException(status_code=500, detail="Experiment execution failed") from exc

        await db.commit()
        await db.refresh(experiment)

    return experiment


@router.get("/{experiment_id}", response_model=ExperimentRead)
async def get_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExperimentRead:
    experiment = await _get_experiment_or_404(experiment_id, current_user, db)
    return experiment


@router.get("/{experiment_id}/status", response_model=ExperimentStatusResponse)
async def get_experiment_status(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExperimentStatusResponse:
    experiment = await _get_experiment_or_404(experiment_id, current_user, db)
    return ExperimentStatusResponse(
        id=experiment.id,
        status=experiment.status,
        result_payload=experiment.result_payload,
        error_message=experiment.error_message,
    )

