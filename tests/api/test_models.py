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


@pytest.mark.asyncio
async def test_broadcasts_and_content_tables_created():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    tables = Base.metadata.tables.keys()
    assert "broadcasts" in tables
    assert "bot_content" in tables
    await engine.dispose()


@pytest.mark.asyncio
async def test_payments_table_created(db):
    from api.models.models import Payment
    from datetime import date
    from decimal import Decimal
    p = Payment(
        user_id=None,
        amount=Decimal("1500.00"),
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        payment_type="monthly",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    assert p.id is not None
    assert p.payment_type == "monthly"
