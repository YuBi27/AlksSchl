from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.crud.broadcasts import save_broadcast, list_broadcasts
from api.schemas.schemas import BroadcastCreate, BroadcastRead

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])


@router.post("", response_model=BroadcastRead, status_code=201)
async def create_broadcast(data: BroadcastCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await save_broadcast(
        db,
        target_type=data.target_type,
        message_type=data.message_type,
        recipient_count=data.recipient_count,
        sender_id=data.sender_id,
        target_id=data.target_id,
        text=data.text,
        file_id=data.file_id,
    )


@router.get("", response_model=list[BroadcastRead])
async def get_broadcasts_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    sender_id: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
):
    return await list_broadcasts(db, sender_id=sender_id, limit=limit)
