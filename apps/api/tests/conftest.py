import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.base import Base, get_db
from app.main import app
from app.models.agent import Agent
from app.models.model_config import ModelConfig
from app.models.role import Role

TEST_DATABASE_URL = "postgresql+asyncpg://futurist:futurist@localhost:5432/futurist_os_test"

# NullPool: each test runs in its own pytest-asyncio event loop, so connections
# must not be pooled/reused across loops (asyncpg connections are loop-bound).
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        session.add_all([Role(slug="admin", name="Administrator"), Role(slug="member", name="Mitglied")])
        model_config = ModelConfig(
            provider="anthropic",
            model_name="claude-haiku-4-5-20251001",
            display_name="Claude Haiku 4.5",
            is_default=True,
            capabilities={"tools": True, "vision": True},
        )
        session.add(model_config)
        await session.flush()
        session.add(
            Agent(
                slug="executive",
                name="Executive Agent",
                system_prompt="Du bist ein hilfreicher Test-Agent.",
                default_model_id=model_config.id,
            )
        )
        await session.commit()

    yield


@pytest_asyncio.fixture(autouse=True)
async def _reset_rate_limits():
    """Rate-limit counters live in real Redis, not the per-test Postgres DB that
    setup_database() resets - without this, tests that each register/login a fresh user
    (most of the suite) would accumulate against the same rate-limit key (ASGITransport
    requests have no real client IP, so every test shares one 'unknown' key) and start
    tripping 429s partway through the suite."""
    redis = Redis.from_url(get_settings().REDIS_URL)
    async for key in redis.scan_iter("ratelimit:*"):
        await redis.delete(key)
    await redis.aclose()
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


@pytest_asyncio.fixture
async def db_session():
    """A raw session for tests that call orchestrator/tool code directly, bypassing HTTP."""
    async with TestSessionLocal() as session:
        yield session


async def register_and_login(client: AsyncClient, email: str = "z@futurist.os") -> str:
    """Registers a fresh user and returns a valid access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": "Z"},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return login.json()["access_token"]
