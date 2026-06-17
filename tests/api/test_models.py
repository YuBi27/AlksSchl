import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from api.models.models import Base


@pytest.mark.asyncio
async def test_all_tables_created():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    tables = Base.metadata.tables.keys()
    assert "users" in tables
    assert "student_profiles" in tables
    assert "teacher_profiles" in tables
    assert "invite_codes" in tables
    assert "agreements" in tables
    assert "admin_actions_log" in tables
    await engine.dispose()
