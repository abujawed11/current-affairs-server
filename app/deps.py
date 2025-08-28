from __future__ import annotations
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import get_db
from .models import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import decode_token
from starlette import status


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


# --- NEW: JWT auth dependency ---
bearer = HTTPBearer(auto_error=False)

async def get_current_user_jwt(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials)
        user_id = int(payload.get("sub") or 0)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User disabled")
    return user