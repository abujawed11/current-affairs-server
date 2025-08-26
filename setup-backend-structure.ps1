# Run this from the parent folder OR inside current-affairs-quiz.
# If you're already inside current-affairs-quiz, you can comment the next line.
if (Test-Path "current-affairs-quiz") { Set-Location current-affairs-quiz }

function New-Dir {
  param([string]$Path)
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function New-FileIfMissing {
  param([string]$Path, [string]$Content = "")
  if (-not (Test-Path $Path)) {
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Dir $dir }
    $Content | Out-File -Encoding UTF8 -FilePath $Path
  }
}

Write-Host "🔧 Creating backend folders..."

# Backend app folders
New-Dir "app"
New-Dir "app/services"
New-Dir "app/routers"

# Optional: keep your seeds folder at root (you may already have this)
New-Dir "seeds"

Write-Host "📝 Creating backend files (with starter boilerplate where useful)..."

# __init__.py
New-FileIfMissing "app/__init__.py" ""

# db.py (async MySQL engine + session)
New-FileIfMissing "app/db.py" @'
from __future__ import annotations
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. mysql+aiomysql://user:pass@127.0.0.1:3306/ca_quiz?charset=utf8mb4
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. See .env.example")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
'@

# models.py (SQLAlchemy models, minimal stubs)
New-FileIfMissing "app/models.py" @'
from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import String, Integer, Text, Boolean, Date, ForeignKey, DateTime, Float, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Test(Base):
    __tablename__ = "tests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    duration_sec: Mapped[int] = mapped_column(Integer, default=1200)

    questions: Mapped[List["Question"]] = relationship(back_populates="test", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(100))
    stem: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)

    test: Mapped["Test"] = relationship(back_populates="questions")
    options: Mapped[List["Option"]] = relationship(back_populates="question", cascade="all, delete-orphan")

class Option(Base):
    __tablename__ = "options"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped["Question"] = relationship(back_populates="options")

class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_taken_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accuracy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[Optional[int]] = mapped_column(ForeignKey("options.id", ondelete="SET NULL"), nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    position: Mapped[int] = mapped_column(Integer)  # 1..N order used in attempt

    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_q"),)
'@

# schemas.py (Pydantic v2 stubs)
New-FileIfMissing "app/schemas.py" @'
from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field

class TestOut(BaseModel):
    id: int
    title: str
    duration_sec: int

class TestDetailOut(BaseModel):
    id: int
    title: str
    duration_sec: int
    question_count: int

class AttemptCreateIn(BaseModel):
    test_id: int

class QuestionOptionOut(BaseModel):
    id: int
    text: str

class QuestionOut(BaseModel):
    id: int
    date: date
    category: str
    stem: str
    options: List[QuestionOptionOut]

class AttemptOut(BaseModel):
    attempt_id: int
    test_id: int
    questions: List[QuestionOut]

class AnswerIn(BaseModel):
    question_id: int
    option_id: int

class SubmitIn(BaseModel):
    time_taken_sec: int

class ReviewOptionOut(BaseModel):
    id: int
    text: str
    is_correct: bool
    selected: bool

class ReviewQuestionOut(BaseModel):
    id: int
    stem: str
    explanation: str
    options: List[ReviewOptionOut]

class ReviewOut(BaseModel):
    attempt_id: int
    score: int
    total: int
    accuracy_pct: float
    questions: List[ReviewQuestionOut]
'@

# deps.py (auth + db dependency)
New-FileIfMissing "app/deps.py" @'
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
'@

# services/scoring.py (simple helpers)
New-FileIfMissing "app/services/scoring.py" @'
def compute_score(correct_flags: list[bool]) -> tuple[int, int, float]:
    total = len(correct_flags)
    score = sum(1 for v in correct_flags if v)
    accuracy = round((score / total) * 100.0, 2) if total else 0.0
    return score, total, accuracy
'@

# routers/tests.py (skeleton)
New-FileIfMissing "app/routers/tests.py" @'
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
'@

# routers/attempts.py (skeleton)
New-FileIfMissing "app/routers/attempts.py" @'
from __future__ import annotations
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_db
from ..models import Test, Question, Option, Attempt, AttemptAnswer
from ..schemas import AttemptCreateIn, AttemptOut, QuestionOut, QuestionOptionOut, AnswerIn, SubmitIn, ReviewOut, ReviewQuestionOut, ReviewOptionOut
from ..deps import get_current_user
from ..services.scoring import compute_score

router = APIRouter(prefix="/attempts", tags=["attempts"])

@router.post("", response_model=AttemptOut)
async def create_attempt(payload: AttemptCreateIn, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    test = await db.get(Test, payload.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    qrows = (await db.execute(select(Question).where(Question.test_id == test.id))).scalars().all()
    if not qrows:
        raise HTTPException(status_code=400, detail="No questions in test")

    # pick/shuffle up to 20
    random.shuffle(qrows)
    qrows = qrows[:20]
    attempt = Attempt(user_id=user.id, test_id=test.id)
    db.add(attempt)
    await db.flush()

    # Maintain order via AttemptAnswer.position, and return options
    out_questions: list[QuestionOut] = []
    for idx, q in enumerate(qrows, start=1):
        db.add(AttemptAnswer(attempt_id=attempt.id, question_id=q.id, position=idx))
        opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
        random.shuffle(opts)
        out_questions.append(QuestionOut(
            id=q.id, date=q.date, category=q.category, stem=q.stem,
            options=[QuestionOptionOut(id=o.id, text=o.text) for o in opts]
        ))

    await db.commit()
    return AttemptOut(attempt_id=attempt.id, test_id=test.id, questions=out_questions)

@router.post("/{attempt_id}/answer")
async def answer(attempt_id: int, payload: AnswerIn, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    # validate attempt belongs to user's test implicitly; (extend with ownership checks if needed)
    att = await db.get(Attempt, attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")
    # validate question in this attempt
    aa = (await db.execute(select(AttemptAnswer).where(
        AttemptAnswer.attempt_id == attempt_id,
        AttemptAnswer.question_id == payload.question_id
    ))).scalar_one_or_none()
    if not aa:
        raise HTTPException(status_code=400, detail="Question not part of this attempt")
    # validate option belongs to question
    opt = await db.get(Option, payload.option_id)
    if not opt or opt.question_id != payload.question_id:
        raise HTTPException(status_code=400, detail="option_id does not belong to question_id")

    aa.option_id = opt.id
    await db.commit()
    return {"ok": True}

@router.post("/{attempt_id}/submit")
async def submit(attempt_id: int, payload: SubmitIn, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    att = await db.get(Attempt, attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # fetch answers and compute correctness
    rows = (await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id))).scalars().all()
    correct_flags: list[bool] = []
    for r in rows:
        if r.option_id is None:
            correct_flags.append(False)
            r.is_correct = False
        else:
            o = await db.get(Option, r.option_id)
            r.is_correct = bool(o.is_correct)
            correct_flags.append(bool(o.is_correct))

    score, total, acc = compute_score(correct_flags)
    from sqlalchemy import func
    att.score = score
    att.total = total
    att.accuracy_pct = acc
    att.time_taken_sec = payload.time_taken_sec
    att.submitted_at = func.now()

    await db.commit()
    return {"attempt_id": att.id, "score": score, "total": total, "accuracy_pct": acc}

@router.get("/{attempt_id}/review", response_model=ReviewOut)
async def review(attempt_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    att = await db.get(Attempt, attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Pull questions in stored order
    aas = (await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id).order_by(AttemptAnswer.position))).scalars().all()
    qouts: list[ReviewQuestionOut] = []
    correct_flags: list[bool] = []

    for aa in aas:
        q = await db.get(Question, aa.question_id)
        opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
        out_opts = []
        for o in opts:
            selected = (aa.option_id == o.id)
            out_opts.append(ReviewOptionOut(id=o.id, text=o.text, is_correct=bool(o.is_correct), selected=selected))
        if aa.is_correct is not None:
            correct_flags.append(bool(aa.is_correct))
        qouts.append(ReviewQuestionOut(id=q.id, stem=q.stem, explanation=q.explanation, options=out_opts))

    # If not submitted yet, compute on the fly
    if att.score is None or att.total is None or att.accuracy_pct is None:
        score, total, acc = compute_score(correct_flags)
    else:
        score, total, acc = att.score, att.total, att.accuracy_pct

    return ReviewOut(attempt_id=att.id, score=score or 0, total=total or len(aas), accuracy_pct=acc or 0.0, questions=qouts)
'@

# main.py (FastAPI app + CORS + routers + create tables)
New-FileIfMissing "app/main.py" @'
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .db import engine
from .models import Base
from .routers.tests import router as tests_router
from .routers.attempts import router as attempts_router

load_dotenv()

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8081, http://127.0.0.1:8081, exp://*, exp+android://*").split(",")]

app = FastAPI(title="Current Affairs Quiz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # Create tables if not present
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(tests_router)
app.include_router(attempts_router)

@app.get("/")
async def root():
    return {"ok": True, "service": "current-affairs-quiz"}
'@

# requirements.txt
New-FileIfMissing "requirements.txt" @'
fastapi==0.115.0
uvicorn[standard]==0.30.6
SQLAlchemy==2.0.35
aiomysql==0.2.0
pydantic==2.8.2
python-dotenv==1.0.1
'@

# .env.example
New-FileIfMissing ".env.example" @'
# MySQL 8 DSN (utf8mb4)
DATABASE_URL="mysql+aiomysql://root:password@127.0.0.1:3306/ca_quiz?charset=utf8mb4"
# CORS origins for Expo dev
CORS_ORIGINS="http://localhost:8081,http://127.0.0.1:8081,exp://*,exp+android://*"
'@

# docker-compose.yml (optional MySQL 8)
New-FileIfMissing "docker-compose.yml" @'
version: "3.9"
services:
  db:
    image: mysql:8.0
    container_name: ca_quiz_db
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: ca_quiz
      MYSQL_USER: causer
      MYSQL_PASSWORD: capass
    command: ["--character-set-server=utf8mb4", "--collation-server=utf8mb4_unicode_ci"]
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h localhost -ppassword || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 10
volumes:
  db_data:
'@

Write-Host "✅ Backend structure created. Next steps:"
Write-Host "1) Copy .env.example to .env and edit DATABASE_URL / CORS_ORIGINS."
Write-Host "2) pip install -r requirements.txt"
Write-Host "3) Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
