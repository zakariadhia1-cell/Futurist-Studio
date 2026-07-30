import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base, get_db
from app.main import app
from app.models.role import Role

TEST_DATABASE_URL = "postgresql+asyncpg://futurist:futurist@localhost:5432/futurist_os_test"

# NullPool: each test runs in its own pytest-asyncio event loop, so connections
# must not be pooled/reused across loops (asyncpg connections are loop-bound).
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        session.add_all([Role(slug="admin", name="Administrator"), Role(slug="member", name="Mitglied")])
        await session.commit()

    yield


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
