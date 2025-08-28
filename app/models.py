# # from __future__ import annotations
# # from datetime import datetime, date, timezone
# # from typing import List, Optional

# # from sqlalchemy import (
# #     String, Integer, Text, Boolean, Date, ForeignKey,
# #     DateTime, Float, UniqueConstraint
# # )
# # from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# # class Base(DeclarativeBase):
# #     pass


# # class User(Base):
# #     __tablename__ = "users"
# #     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
# #     device_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
# #     # Store UTC-aware timestamp
# #     created_at: Mapped[datetime] = mapped_column(
# #         DateTime(timezone=True),
# #         default=lambda: datetime.now(timezone.utc),
# #         nullable=False,
# #     )


# # class Test(Base):
# #     __tablename__ = "tests"
# #     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
# #     title: Mapped[str] = mapped_column(String(255), unique=True, index=True)
# #     duration_sec: Mapped[int] = mapped_column(Integer, default=1200)

# #     questions: Mapped[List["Question"]] = relationship(
# #         back_populates="test", cascade="all, delete-orphan"
# #     )


# # class Question(Base):
# #     __tablename__ = "questions"
# #     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
# #     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
# #     date: Mapped[date] = mapped_column(Date)
# #     category: Mapped[str] = mapped_column(String(100))
# #     stem: Mapped[str] = mapped_column(Text)
# #     explanation: Mapped[str] = mapped_column(Text)

# #     test: Mapped["Test"] = relationship(back_populates="questions")
# #     options: Mapped[List["Option"]] = relationship(
# #         back_populates="question", cascade="all, delete-orphan"
# #     )


# # class Option(Base):
# #     __tablename__ = "options"
# #     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
# #     question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
# #     text: Mapped[str] = mapped_column(Text)
# #     is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

# #     question: Mapped["Question"] = relationship(back_populates="options")


# # class Attempt(Base):
# #     __tablename__ = "attempts"
# #     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
# #     user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
# #     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)

# #     # ✅ Use UTC-aware Python default so server/device timezones don’t matter
# #     started_at: Mapped[datetime] = mapped_column(
# #         DateTime(timezone=True),
# #         default=lambda: datetime.now(timezone.utc),
# #         nullable=False,
# #     )

# #     submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
# #     time_taken_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
# #     score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
# #     total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
# #     accuracy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


# # class AttemptAnswer(Base):
# #     __tablename__ = "attempt_answers"
# #     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
# #     attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
# #     question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
# #     option_id: Mapped[Optional[int]] = mapped_column(ForeignKey("options.id", ondelete="SET NULL"), nullable=True)
# #     is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
# #     position: Mapped[int] = mapped_column(Integer)  # 1..N order used in attempt

# #     __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_q"),)





# # app/models.py
# from __future__ import annotations
# from datetime import datetime, date, timezone
# from typing import List, Optional

# from sqlalchemy import (
#     String, Integer, Text, Boolean, Date, ForeignKey,
#     DateTime, Float, UniqueConstraint
# )
# from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# class Base(DeclarativeBase):
#     pass


# class User(Base):
#     __tablename__ = "users"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     # Optional device-based identity (kept from your existing code)
#     device_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)

#     # 👇 New auth fields
#     username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
#     email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
#     password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

#     # Store UTC-aware timestamp
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc),
#         nullable=False,
#     )

#     # Relationship for /me/attempts, etc.
#     attempts: Mapped[List["Attempt"]] = relationship(
#         back_populates="user", cascade="all, delete-orphan"
#     )


# class Test(Base):
#     __tablename__ = "tests"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     title: Mapped[str] = mapped_column(String(255), unique=True, index=True)
#     duration_sec: Mapped[int] = mapped_column(Integer, default=1200)

#     questions: Mapped[List["Question"]] = relationship(
#         back_populates="test", cascade="all, delete-orphan"
#     )


# class Question(Base):
#     __tablename__ = "questions"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
#     date: Mapped[date] = mapped_column(Date)
#     category: Mapped[str] = mapped_column(String(100))
#     stem: Mapped[str] = mapped_column(Text)
#     explanation: Mapped[str] = mapped_column(Text)

#     test: Mapped["Test"] = relationship(back_populates="questions")
#     options: Mapped[List["Option"]] = relationship(
#         back_populates="question", cascade="all, delete-orphan"
#     )


# class Option(Base):
#     __tablename__ = "options"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
#     text: Mapped[str] = mapped_column(Text)
#     is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

#     question: Mapped["Question"] = relationship(back_populates="options")


# class Attempt(Base):
#     __tablename__ = "attempts"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
#     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)

#     # ✅ Use UTC-aware Python default so server/device timezones don’t matter
#     started_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc),
#         nullable=False,
#     )

#     submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
#     time_taken_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     accuracy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

#     user: Mapped["User"] = relationship(back_populates="attempts")


# class AttemptAnswer(Base):
#     __tablename__ = "attempt_answers"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
#     question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
#     option_id: Mapped[Optional[int]] = mapped_column(ForeignKey("options.id", ondelete="SET NULL"), nullable=True)
#     is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
#     position: Mapped[int] = mapped_column(Integer)  # 1..N order used in attempt

#     __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_q"),)





# from __future__ import annotations
# from datetime import datetime, date, timezone
# from typing import List, Optional

# from sqlalchemy import (
#     String, Integer, Text, Boolean, Date, ForeignKey,
#     DateTime, Float, UniqueConstraint, Computed
# )
# from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# class Base(DeclarativeBase):
#     pass


# # =========================
# #        MODELS
# # =========================

# class User(Base):
#     __tablename__ = "users"

#     # Internal fast PK (kept as int)
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     # Public code (auto-computed from id): USR000001
#     userId: Mapped[str] = mapped_column(
#         String(16),
#         Computed("concat('USR', lpad(id, 6, '0'))", persisted=True),
#         unique=True,
#         index=True,
#     )

#     # Optional device identity (kept from your setup)
#     device_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)

#     # Auth fields
#     username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
#     email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
#     password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

#     # UTC-aware timestamp
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc),
#         nullable=False,
#     )

#     # Relationships
#     attempts: Mapped[List["Attempt"]] = relationship(
#         back_populates="user", cascade="all, delete-orphan"
#     )


# class Test(Base):
#     __tablename__ = "tests"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     # Public code: TEST000001
#     testId: Mapped[str] = mapped_column(
#         String(20),
#         Computed("concat('TEST', lpad(id, 6, '0'))", persisted=True),
#         unique=True,
#         index=True,
#     )

#     title: Mapped[str] = mapped_column(String(255), unique=True, index=True)
#     duration_sec: Mapped[int] = mapped_column(Integer, default=1200)

#     questions: Mapped[List["Question"]] = relationship(
#         back_populates="test", cascade="all, delete-orphan"
#     )


# class Question(Base):
#     __tablename__ = "questions"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     # Public code: QUS000001
#     questionId: Mapped[str] = mapped_column(
#         String(16),
#         Computed("concat('QUS', lpad(id, 6, '0'))", persisted=True),
#         unique=True,
#         index=True,
#     )

#     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
#     date: Mapped[date] = mapped_column(Date)
#     category: Mapped[str] = mapped_column(String(100))
#     stem: Mapped[str] = mapped_column(Text)
#     explanation: Mapped[str] = mapped_column(Text)

#     test: Mapped["Test"] = relationship(back_populates="questions")
#     options: Mapped[List["Option"]] = relationship(
#         back_populates="question", cascade="all, delete-orphan"
#     )


# class Option(Base):
#     __tablename__ = "options"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     # Public code: OPT000001
#     optionId: Mapped[str] = mapped_column(
#         String(16),
#         Computed("concat('OPT', lpad(id, 6, '0'))", persisted=True),
#         unique=True,
#         index=True,
#     )

#     question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
#     text: Mapped[str] = mapped_column(Text)
#     is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

#     question: Mapped["Question"] = relationship(back_populates="options")


# class Attempt(Base):
#     __tablename__ = "attempts"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     # Public code: ATT000001
#     attemptId: Mapped[str] = mapped_column(
#         String(16),
#         Computed("concat('ATT', lpad(id, 6, '0'))", persisted=True),
#         unique=True,
#         index=True,
#     )

#     user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
#     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)

#     started_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc),
#         nullable=False,
#     )

#     submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
#     time_taken_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     accuracy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

#     user: Mapped["User"] = relationship(back_populates="attempts")


# class AttemptAnswer(Base):
#     __tablename__ = "attempt_answers"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     # Public code: AANS000001
#     attemptAnswerId: Mapped[str] = mapped_column(
#         String(20),
#         Computed("concat('AANS', lpad(id, 6, '0'))", persisted=True),
#         unique=True,
#         index=True,
#     )

#     attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
#     question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
#     option_id: Mapped[Optional[int]] = mapped_column(ForeignKey("options.id", ondelete="SET NULL"), nullable=True)
#     is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
#     position: Mapped[int] = mapped_column(Integer)  # 1..N order used in attempt

#     __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_q"),)



from __future__ import annotations
from datetime import datetime, date, timezone
from typing import List, Optional

from sqlalchemy import (
    String, Integer, Text, Boolean, Date, ForeignKey,
    DateTime, Float, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base   # <-- use the global Base
# class Base(DeclarativeBase):
#     pass


# =========================
#        MODELS
# =========================

class User(Base):
    __tablename__ = "users"

    # Internal fast PK (int)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Public code (set in app code after flush)
    userId: Mapped[Optional[str]] = mapped_column(String(16), unique=True, index=True, nullable=True)

    # Optional device identity
    device_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)

    # Auth fields
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # UTC-aware timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    attempts: Mapped[List["Attempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Public code (set after flush)
    testId: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    duration_sec: Mapped[int] = mapped_column(Integer, default=1200)

    questions: Mapped[List["Question"]] = relationship(
        back_populates="test", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Public code (set after flush)
    questionId: Mapped[Optional[str]] = mapped_column(String(16), unique=True, index=True, nullable=True)

    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(100))
    stem: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)

    test: Mapped["Test"] = relationship(back_populates="questions")
    options: Mapped[List["Option"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Public code (set after flush)
    optionId: Mapped[Optional[str]] = mapped_column(String(16), unique=True, index=True, nullable=True)

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped["Question"] = relationship(back_populates="options")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Public code (set after flush)
    attemptId: Mapped[Optional[str]] = mapped_column(String(16), unique=True, index=True, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_taken_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Changed from Integer to Float
    total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accuracy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship(back_populates="attempts")


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Public code (set after flush)
    attemptAnswerId: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)

    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[Optional[int]] = mapped_column(ForeignKey("options.id", ondelete="SET NULL"), nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    position: Mapped[int] = mapped_column(Integer)  # 1..N order used in attempt

    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_q"),)
