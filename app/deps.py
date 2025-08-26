from __future__ import annotations
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import get_db
from .models import User

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
):
    if not x_device_id:
        raise HTTPException(status_code=401, detail="X-Device-Id header required")
    # create-or-get
    result = await db.execute(select(User).where(User.device_id == x_device_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(device_id=x_device_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
