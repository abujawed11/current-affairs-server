# from __future__ import annotations
# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func
# from ..db import get_db
# from ..models import Test, Question
# from ..schemas import TestOut, TestDetailOut

# router = APIRouter(prefix="/tests", tags=["tests"])

# @router.get("", response_model=list[TestOut])
# async def list_tests(db: AsyncSession = Depends(get_db)):
#     rows = (await db.execute(select(Test))).scalars().all()
#     return [TestOut(id=r.id, title=r.title, duration_sec=r.duration_sec) for r in rows]

# @router.get("/{test_id}", response_model=TestDetailOut)
# async def get_test(test_id: int, db: AsyncSession = Depends(get_db)):
#     t = await db.get(Test, test_id)
#     if not t:
#         from fastapi import HTTPException
#         raise HTTPException(status_code=404, detail="Test not found")
#     qcount = await db.scalar(select(func.count()).select_from(Question).where(Question.test_id == test_id))
#     return TestDetailOut(id=t.id, title=t.title, duration_sec=t.duration_sec, question_count=int(qcount or 0))




# app/routers/tests.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from ..db import get_db
from ..models import Test, Question, Attempt
from ..schemas import TestOut, TestDetailOut
from ..services.codes import make_code  # optional if you create tests here
from ..deps import get_current_user_jwt


router = APIRouter(prefix="/tests", tags=["tests"])

# @router.get("", response_model=list[TestOut])
# async def list_tests(db: AsyncSession = Depends(get_db)):
#     rows = (await db.execute(select(Test))).scalars().all()
#     # ensure codes exist (for legacy rows)
#     for r in rows:
#         if not r.testId:
#             r.testId = make_code("TEST", r.id)
#     await db.commit()
#     return [TestOut(testId=r.testId, title=r.title, duration_sec=r.duration_sec) for r in rows]

# @router.get("", response_model=list[TestOut])
# async def list_tests(db: AsyncSession = Depends(get_db), user=Depends(get_current_user_jwt)):
#     tests = (await db.execute(select(Test))).scalars().all()
#     out: list[TestOut] = []

#     for t in tests:
#         # last submitted attempt by this user for this test
#         last = (await db.execute(
#             select(Attempt).where(
#                 Attempt.user_id == user.id,
#                 Attempt.test_id == t.id,
#                 Attempt.submitted_at.is_not(None),
#             ).order_by(desc(Attempt.submitted_at)).limit(1)
#         )).scalar_one_or_none()

#         last_attempt = None
#         if last and last.accuracy_pct is not None:
#             # you have codes on Attempt model as attemptId
#             last_attempt = {"attemptId": last.attemptId, "accuracy_pct": float(last.accuracy_pct)}

#         out.append(TestOut(
#             testId=t.testId, title=t.title, duration_sec=t.duration_sec, last_attempt=last_attempt
#         ))
#     return out

router = APIRouter(prefix="/tests", tags=["tests"])

def normalize_category(category: str) -> str:
    """Normalize backend categories to match frontend category keys"""
    category_mapping = {
        "Economy": "economy",
        "International": "current_affairs", 
        "Science & Tech": "science_tech",
        "National": "polity",
        "Environment": "environment",
        "Sports": "sports_awards",
        "Awards": "sports_awards", 
        "Govt Schemes": "polity",
        "History": "history",
        "Geography": "geography",
        "Art & Culture": "art_culture",
        "Static GK": "static_gk",
        "Current Affairs": "current_affairs",
        "Polity": "polity",
        "Science": "science_tech",
        "Technology": "science_tech"
    }
    return category_mapping.get(category, category.lower().replace(" ", "_"))

@router.get("", response_model=list[TestOut])
async def list_tests(db: AsyncSession = Depends(get_db), user=Depends(get_current_user_jwt)):
    tests = (await db.execute(select(Test))).scalars().all()
    out: list[TestOut] = []
    for t in tests:
        if not t.testId:
            t.testId = make_code("TEST", t.id)
        
        # Use the test's category directly, with normalization
        primary_category = normalize_category(t.category) if t.category else None
        
        # latest submitted attempt for this user & test
        last = (await db.execute(
            select(Attempt).where(
                Attempt.user_id == user.id,
                Attempt.test_id == t.id,
                Attempt.submitted_at.is_not(None),
            ).order_by(desc(Attempt.submitted_at)).limit(1)
        )).scalar_one_or_none()
        last_attempt = None
        if last and last.accuracy_pct is not None:
            last_attempt = {"attemptId": last.attemptId, "accuracy_pct": float(last.accuracy_pct)}
        out.append(TestOut(
            testId=t.testId, 
            title=t.title, 
            duration_sec=t.duration_sec, 
            category=primary_category,
            last_attempt=last_attempt
        ))
    await db.commit()
    return out

@router.get("/{testId}", response_model=TestDetailOut)
async def get_test(testId: str, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(Test).where(Test.testId == testId))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Test not found")
    qcount = await db.scalar(select(func.count()).select_from(Question).where(Question.test_id == t.id))
    return TestDetailOut(testId=t.testId, title=t.title, duration_sec=t.duration_sec, question_count=int(qcount or 0))
