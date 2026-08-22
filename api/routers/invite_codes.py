import secrets
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import InviteCodeOut, InviteCodeUseRequest
from api.crud.invite_codes import get_invite_code, use_invite_code, is_code_valid, create_invite_code
from api.crud.users import update_user_role

router = APIRouter(prefix="/invite-codes", tags=["invite-codes"])


class InviteCodeCreate(BaseModel):
    created_by: Optional[int] = None
    role: str = "teacher"


@router.post("", response_model=InviteCodeOut)
async def generate_invite_code(
    body: InviteCodeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    code = secrets.token_urlsafe(8)
    invite = await create_invite_code(db, code=code, created_by=body.created_by, role=body.role)
    return invite


@router.get("/{code}", response_model=InviteCodeOut)
async def validate_code(code: str, db: Annotated[AsyncSession, Depends(get_db)]):
    invite = await get_invite_code(db, code)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite code not found")
    if not is_code_valid(invite):
        raise HTTPException(status_code=410, detail="Invite code is expired or already used")
    return invite


@router.post("/{code}/use", response_model=InviteCodeOut)
async def use_code(
    code: str,
    body: InviteCodeUseRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    invite = await use_invite_code(db, code, body.user_id)
    if not invite:
        raise HTTPException(status_code=410, detail="Invite code is invalid or already used")
    await update_user_role(db, body.user_id, invite.role)
    return invite
