"""Regression: registration must not be intercepted by the blocked router.

A user who is still filling the registration form (status "new") sends text
messages (ПІБ, дата народження, телефон...). BlockedStatusFilter must pass
those through to the dialog. Only "pending" (заявка подана) and "banned"
messages are intercepted.
"""
import pytest
from bot.handlers.blocked import BlockedStatusFilter


@pytest.mark.asyncio
@pytest.mark.parametrize("status,expected", [
    ("new", False),        # ще заповнює форму — НЕ блокувати
    ("active", False),
    ("pending", True),     # заявка подана — чекає рішення
    ("banned", True),
])
async def test_blocked_filter_by_status(status, expected):
    f = BlockedStatusFilter()
    result = await f(message=None, user_data={"status": status})
    assert result is expected


@pytest.mark.asyncio
async def test_blocked_filter_no_user_data():
    f = BlockedStatusFilter()
    assert await f(message=None, user_data=None) is False
