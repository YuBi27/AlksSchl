import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from api.models.models import Base
from api.db import get_db
from api.main import app
from unittest.mock import patch

TEST_DB = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db):
    async def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db

    with patch("api.security.settings") as mock_settings:
        mock_settings.bot_secret = "test-secret"
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Bot-Secret": "test-secret"},
        ) as ac:
            yield ac
    app.dependency_overrides.clear()
