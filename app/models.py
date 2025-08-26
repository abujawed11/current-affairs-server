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
