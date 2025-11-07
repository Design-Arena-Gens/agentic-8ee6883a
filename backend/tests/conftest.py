from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def async_session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture()
async def client(async_session_factory):
    async def _get_test_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def clean_database(test_engine):
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
