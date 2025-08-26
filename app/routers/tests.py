from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..db import get_db
from ..models import Test, Question
from ..schemas import TestOut, TestDetailOut

router = APIRouter(prefix="/tests", tags=["tests"])

@router.get("", response_model=list[TestOut])
async def list_tests(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Test))).scalars().all()
    return [TestOut(id=r.id, title=r.title, duration_sec=r.duration_sec) for r in rows]

@router.get("/{test_id}", response_model=TestDetailOut)
async def get_test(test_id: int, db: AsyncSession = Depends(get_db)):
    t = await db.get(Test, test_id)
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Test not found")
    qcount = await db.scalar(select(func.count()).select_from(Question).where(Question.test_id == test_id))
    return TestDetailOut(id=t.id, title=t.title, duration_sec=t.duration_sec, question_count=int(qcount or 0))
