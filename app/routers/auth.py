# # app/routers/auth.py
# from __future__ import annotations
# from fastapi import APIRouter, HTTPException, Depends
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from starlette import status

# from ..db import get_db
# from ..models import User
# from ..schemas import SignupIn, LoginIn, AuthOut, UserOut
# from ..security import hash_password, verify_password, create_access_token

# router = APIRouter(prefix="/auth", tags=["auth"])

# @router.post("/signup", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
# async def signup(body: SignupIn, db: AsyncSession = Depends(get_db)):
#     # check username/email uniqueness
#     q = await db.execute(
#         select(User).where((User.username == body.username) | (User.email == body.email))
#     )
#     existing = q.scalar_one_or_none()
#     if existing:
#         if existing.username == body.username:
#             raise HTTPException(400, detail="Username already taken")
#         raise HTTPException(400, detail="Email already registered")

#     user = User(
#         username=body.username.strip(),
#         email=body.email.lower().strip(),
#         password_hash=hash_password(body.password),
#         is_active=True,
#     )
#     db.add(user)
#     await db.flush()  # to get user.id
#     token = create_access_token(user.id)
#     await db.commit()
#     return AuthOut(token=token, user=UserOut(id=user.id, username=user.username, email=user.email))

# @router.post("/login", response_model=AuthOut)
# async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
#     q = await db.execute(select(User).where(User.username == body.username))
#     user = q.scalar_one_or_none()
#     if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
#     if not user.is_active:
#         raise HTTPException(status_code=403, detail="User is inactive")

#     token = create_access_token(user.id)
#     return AuthOut(token=token, user=UserOut(id=user.id, username=user.username, email=user.email))



# app/routers/auth.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..db import get_db
from ..models import User
from ..schemas import SignupIn, LoginIn, AuthOut, UserOut
from ..security import hash_password, verify_password, create_access_token
from ..services.codes import make_code

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupIn, db: AsyncSession = Depends(get_db)):
    # check username/email uniqueness
    q = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    existing = q.scalar_one_or_none()
    if existing:
        if existing.username == body.username:
            raise HTTPException(400, detail="Username already taken")
        raise HTTPException(400, detail="Email already registered")

    user = User(
        username=body.username.strip(),
        email=body.email.lower().strip(),
        password_hash=hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()  # get user.id
    # 👇 set public code
    user.userId = make_code("USR", user.id)
    token = create_access_token(user.id)
    await db.commit()
    await db.refresh(user)

    return AuthOut(
        token=token,
        user=UserOut(userId=user.userId, username=user.username or "", email=user.email or "")
    )

@router.post("/login", response_model=AuthOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.username == body.username))
    user = q.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    token = create_access_token(user.id)
    # ensure userId exists (in case legacy rows exist)
    if not user.userId:
        user.userId = make_code("USR", user.id)
        await db.commit()
        await db.refresh(user)

    return AuthOut(
        token=token,
        user=UserOut(userId=user.userId, username=user.username or "", email=user.email or "")
    )
