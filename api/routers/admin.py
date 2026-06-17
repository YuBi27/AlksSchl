from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import AdminLogCreate
from api.crud.admin_log import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/log")
async def add_log(
    body: AdminLogCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    entry = await log_action(db, body.admin_id, body.action, body.target_user_id, body.details)
    return {"id": entry.id}
