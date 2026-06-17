import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.services.api_client import APIClient


def make_mock_resp(status=200, json_data=None):
    mock_resp = AsyncMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    mock_resp.raise_for_status = MagicMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data or {})
    return mock_resp


@pytest.mark.asyncio
async def test_get_or_create_user_returns_dict():
    client = APIClient(base_url="http://test", secret="secret")
    mock_resp = make_mock_resp(json_data={"id": 1, "telegram_id": 123, "role": "student", "status": "pending"})
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    client._session = mock_session

    result = await client.get_or_create_user(123, "alice")
    assert result["telegram_id"] == 123
    assert result["role"] == "student"


@pytest.mark.asyncio
async def test_validate_invite_code_not_found():
    client = APIClient(base_url="http://test", secret="secret")
    mock_resp = make_mock_resp(status=404)
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    client._session = mock_session

    result = await client.validate_invite_code("BADCODE")
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_validate_invite_code_already_used():
    client = APIClient(base_url="http://test", secret="secret")
    mock_resp = make_mock_resp(status=410)
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    client._session = mock_session

    result = await client.validate_invite_code("USEDCODE")
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_validate_invite_code_valid():
    client = APIClient(base_url="http://test", secret="secret")
    mock_resp = make_mock_resp(status=200, json_data={"id": 1, "code": "GOOD", "role": "teacher"})
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    client._session = mock_session

    result = await client.validate_invite_code("GOOD")
    assert result["valid"] is True
    assert result["code"] == "GOOD"
