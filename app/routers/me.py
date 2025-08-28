# # app/routers/me.py
# from __future__ import annotations
# from fastapi import APIRouter, Depends
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from ..db import get_db
# from ..deps import get_current_user_jwt
# from ..models import Attempt, Test, User
# from ..schemas import AttemptSummary

# router = APIRouter(prefix="/me", tags=["me"])

# @router.get("/attempts", response_model=list[AttemptSummary])
# async def my_attempts(
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user_jwt),
# ):
#     stmt = (
#         select(
#             Attempt.id,
#             Attempt.test_id,
#             Test.title,
#             Attempt.score,
#             Attempt.total,
#             Attempt.accuracy_pct,
#             Attempt.submitted_at,
#         )
#         .join(Test, Test.id == Attempt.test_id)
#         .where(Attempt.user_id == user.id, Attempt.submitted_at.is_not(None))
#         .order_by(Attempt.submitted_at.desc())
#     )
#     rows = (await db.execute(stmt)).all()
#     return [
#         AttemptSummary(
#             id=r.id,
#             test_id=r.test_id,
#             title=r.title,
#             score=r.score or 0,
#             total=r.total or 0,
#             accuracy_pct=float(r.accuracy_pct or 0.0),
#             submitted_at=r.submitted_at,
#         )
#         for r in rows
#     ]





# app/routers/me.py
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..deps import get_current_user_jwt
from ..models import Attempt, Test, User
from ..schemas import AttemptSummary
from ..services.codes import make_code

router = APIRouter(prefix="/me", tags=["me"])

@router.get("/attempts", response_model=list[AttemptSummary])
async def my_attempts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_jwt),
):
    stmt = (
        select(
            Attempt.id,
            Attempt.attemptId,
            Attempt.test_id,
            Test.testId,
            Test.title,
            Attempt.score,
            Attempt.total,
            Attempt.accuracy_pct,
            Attempt.submitted_at,
        )
        .join(Test, Test.id == Attempt.test_id)
        .where(Attempt.user_id == user.id, Attempt.submitted_at.is_not(None))
        .order_by(Attempt.submitted_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    # ensure codes exist (legacy-safe)
    out: list[AttemptSummary] = []
    for r in rows:
        attempt_code = r.attemptId or make_code("ATT", r.id)
        test_code = r.testId or make_code("TEST", r.test_id)
        out.append(AttemptSummary(
            attemptId=attempt_code,
            testId=test_code,
            title=r.title,
            score=r.score or 0,
            total=r.total or 0,
            accuracy_pct=float(r.accuracy_pct or 0.0),
            submitted_at=r.submitted_at,
        ))
    # optional: persist backfilled codes
    await db.commit()
    return out


@router.get("/inprogress")
async def inprogress(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_jwt),
):
    row = (await db.execute(
        select(Attempt, Test)
        .join(Test, Test.id == Attempt.test_id)
        .where(Attempt.user_id == user.id, Attempt.submitted_at.is_(None))
        .order_by(Attempt.started_at.desc())
        .limit(1)
    )).first()
    if not row:
        return None
    att, test = row
    return {
        "attemptId": att.attemptId,
        "testId": test.testId,
        "title": test.title,
        "started_at": att.started_at,
    }
