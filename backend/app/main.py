from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import Base, engine

settings = get_settings()


def create_application() -> FastAPI:
    application = FastAPI(title=settings.app_name)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.on_event("startup")
    async def on_startup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    return application


app = create_application()

