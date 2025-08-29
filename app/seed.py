# from __future__ import annotations
# import asyncio
# import json
# import sys
# from dataclasses import dataclass
# from datetime import datetime
# from typing import List

# from dotenv import load_dotenv
# import os
# import sqlalchemy as sa
# from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
# from sqlalchemy.ext.asyncio import create_async_engine

# # Import your app's models/engine
# from .db import engine as app_engine  # reuse the engine config from app/db.py
# from .models import Base, Test, Question, Option

# load_dotenv()

# # ---------- Pydantic-free light validation dataclasses ----------
# @dataclass
# class OptionIn:
#     text: str
#     is_correct: bool

# @dataclass
# class QuestionIn:
#     date: str
#     category: str
#     stem: str
#     explanation: str
#     options: List[OptionIn]

# @dataclass
# class TestIn:
#     title: str
#     duration_sec: int
#     questions: List[QuestionIn]

# # ---------- Validation ----------
# def _to_bool(v) -> bool:
#     if isinstance(v, bool):
#         return v
#     if isinstance(v, str):
#         return v.strip().lower() in {"true", "1", "yes", "y"}
#     return bool(v)

# def validate_payload(obj: dict) -> TestIn:
#     for k in ("title", "duration_sec", "questions"):
#         if k not in obj:
#             raise ValueError(f"Missing key: {k}")

#     title = str(obj["title"]).strip()
#     duration_sec = int(obj["duration_sec"])
#     raw_qs = obj["questions"]
#     if not title:
#         raise ValueError("title must be non-empty")
#     if duration_sec <= 0:
#         raise ValueError("duration_sec must be > 0")
#     if not isinstance(raw_qs, list) or not raw_qs:
#         raise ValueError("questions must be a non-empty array")

#     questions: List[QuestionIn] = []
#     for i, q in enumerate(raw_qs, start=1):
#         for k in ("date", "category", "stem", "explanation", "options"):
#             if k not in q:
#                 raise ValueError(f"Question #{i} missing '{k}'")
#         # date
#         try:
#             datetime.strptime(q["date"], "%Y-%m-%d")
#         except Exception:
#             raise ValueError(f"Question #{i} invalid date: {q['date']} (YYYY-MM-DD expected)")
#         # options
#         opts_raw = q["options"]
#         if not isinstance(opts_raw, list) or len(opts_raw) != 4:
#             raise ValueError(f"Question #{i} must have exactly 4 options")
#         opts: List[OptionIn] = []
#         true_count = 0
#         for j, o in enumerate(opts_raw, start=1):
#             if "text" not in o or "is_correct" not in o:
#                 raise ValueError(f"Question #{i} option #{j} missing text/is_correct")
#             text = str(o["text"]).strip()
#             if not text:
#                 raise ValueError(f"Question #{i} option #{j} text empty")
#             is_corr = _to_bool(o["is_correct"])
#             if is_corr:
#                 true_count += 1
#             opts.append(OptionIn(text=text, is_correct=is_corr))
#         if true_count != 1:
#             raise ValueError(f"Question #{i} must have exactly 1 correct option, has {true_count}")

#         questions.append(
#             QuestionIn(
#                 date=q["date"],
#                 category=str(q["category"]).strip(),
#                 stem=str(q["stem"]).strip(),
#                 explanation=str(q["explanation"]).strip(),
#                 options=opts,
#             )
#         )

#     return TestIn(title=title, duration_sec=duration_sec, questions=questions)

# # ---------- Insert ----------
# async def insert_test(session: AsyncSession, payload: TestIn) -> int:
#     # idempotency by unique title
#     existing = await session.scalar(sa.select(Test).where(Test.title == payload.title))
#     if existing:
#         raise ValueError(f"Test with title '{payload.title}' already exists (id={existing.id}).")

#     t = Test(title=payload.title, duration_sec=payload.duration_sec)
#     session.add(t)
#     await session.flush()  # get id

#     for q in payload.questions:
#         qrow = Question(
#             test_id=t.id,
#             date=datetime.strptime(q.date, "%Y-%m-%d").date(),
#             category=q.category,
#             stem=q.stem,
#             explanation=q.explanation,
#         )
#         session.add(qrow)
#         await session.flush()
#         for o in q.options:
#             session.add(Option(question_id=qrow.id, text=o.text, is_correct=o.is_correct))
#     return t.id

# # ---------- CLI ----------
# async def main():
#     if len(sys.argv) < 2:
#         print("Usage: python -m app.seed <path-to-seed-json>")
#         sys.exit(1)

#     json_path = sys.argv[1]
#     if not os.path.exists(json_path):
#         print(f"Seed file not found: {json_path}")
#         sys.exit(1)

#     with open(json_path, "r", encoding="utf-8") as f:
#         raw = json.load(f)

#     # Support either a single test object OR an array of tests
#     seeds = raw if isinstance(raw, list) else [raw]

#     # Create tables if needed
#     async with app_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

#     Session = async_sessionmaker(app_engine, expire_on_commit=False)
#     async with Session() as session:
#         try:
#             async with session.begin():
#                 for s in seeds:
#                     payload = validate_payload(s)
#                     test_id = await insert_test(session, payload)
#                     print(f"✅ Imported '{payload.title}' (id={test_id}) with {len(payload.questions)} questions.")

#         finally:
#         # 👇 ensure connections are closed before the loop ends
#             await app_engine.dispose()
#         # except Exception as e:
#         #     await session.rollback()
#         #     raise

# if __name__ == "__main__":
#     asyncio.run(main())




from __future__ import annotations
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
import os
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

# Import your app's engine/models/helpers
from .db import engine as app_engine  # reuse the engine config from app/db.py
from .models import Base, Test, Question, Option
from .services.codes import make_code  # 👈 generate TEST/QUS/OPT codes

load_dotenv()

# ---------- Pydantic-free light validation dataclasses ----------
@dataclass
class OptionIn:
    text: str
    is_correct: bool

@dataclass
class QuestionIn:
    stem: str
    explanation: str
    options: List[OptionIn]

@dataclass
class TestIn:
    title: str
    duration_sec: int
    category: Optional[str]
    date: Optional[str]  # YYYY-MM-DD format
    questions: List[QuestionIn]

# ---------- Validation ----------
def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"true", "1", "yes", "y"}
    return bool(v)

def validate_payload(obj: dict) -> TestIn:
    for k in ("title", "duration_sec", "questions"):
        if k not in obj:
            raise ValueError(f"Missing key: {k}")

    title = str(obj["title"]).strip()
    duration_sec = int(obj["duration_sec"])
    category = obj.get("category")  # Optional field
    if category:
        category = str(category).strip()
    
    # Handle test-level date
    test_date = obj.get("date")  # Optional field
    if test_date:
        test_date = str(test_date).strip()
        # Validate date format
        try:
            datetime.strptime(test_date, "%Y-%m-%d")
        except Exception:
            raise ValueError(f"Invalid test date format: {test_date} (YYYY-MM-DD expected)")
    
    raw_qs = obj["questions"]
    if not title:
        raise ValueError("title must be non-empty")
    if duration_sec <= 0:
        raise ValueError("duration_sec must be > 0")
    if not isinstance(raw_qs, list) or not raw_qs:
        raise ValueError("questions must be a non-empty array")

    questions: List[QuestionIn] = []
    for i, q in enumerate(raw_qs, start=1):
        for k in ("stem", "explanation", "options"):
            if k not in q:
                raise ValueError(f"Question #{i} missing '{k}'")        
        # No individual date validation needed - using test-level date
        # options
        opts_raw = q["options"]
        if not isinstance(opts_raw, list) or len(opts_raw) != 4:
            raise ValueError(f"Question #{i} must have exactly 4 options")
        opts: List[OptionIn] = []
        true_count = 0
        for j, o in enumerate(opts_raw, start=1):
            if "text" not in o or "is_correct" not in o:
                raise ValueError(f"Question #{i} option #{j} missing text/is_correct")
            text = str(o["text"]).strip()
            if not text:
                raise ValueError(f"Question #{i} option #{j} text empty")
            is_corr = _to_bool(o["is_correct"])
            if is_corr:
                true_count += 1
            opts.append(OptionIn(text=text, is_correct=is_corr))
        if true_count != 1:
            raise ValueError(f"Question #{i} must have exactly 1 correct option, has {true_count}")

        questions.append(
            QuestionIn(
                stem=str(q["stem"]).strip(),
                explanation=str(q["explanation"]).strip(),
                options=opts,
            )
        )

    return TestIn(title=title, duration_sec=duration_sec, category=category, date=test_date, questions=questions)

# ---------- Insert ----------
async def insert_test(session: AsyncSession, payload: TestIn) -> tuple[int, str]:
    # idempotency by unique title
    existing = await session.scalar(sa.select(Test).where(Test.title == payload.title))
    if existing:
        raise ValueError(f"Test with title '{payload.title}' already exists (id={existing.id}, testId={existing.testId}).")

    # Create Test
    test_date_obj = datetime.strptime(payload.date, "%Y-%m-%d").date() if payload.date else None
    t = Test(
        title=payload.title, 
        duration_sec=payload.duration_sec, 
        category=payload.category,
        date=test_date_obj
    )
    session.add(t)
    await session.flush()                 # get t.id
    t.testId = make_code("TEST", t.id)    # 👈 set code

    # Create Questions + Options
    for q in payload.questions:
        qrow = Question(
            test_id=t.id,
            date=test_date_obj or datetime.now().date(),  # Use test date or current date
            category=payload.category or "general",  # Use test category or default
            stem=q.stem,
            explanation=q.explanation,
        )
        session.add(qrow)
        await session.flush()                 # get qrow.id
        qrow.questionId = make_code("QUS", qrow.id)  # 👈 set code

        for o in q.options:
            orow = Option(question_id=qrow.id, text=o.text, is_correct=o.is_correct)
            session.add(orow)
            await session.flush()                 # get orow.id
            orow.optionId = make_code("OPT", orow.id)  # 👈 set code

    # You can commit outside, but returning both ids is useful
    return t.id, t.testId

# ---------- CLI ----------
async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.seed <path-to-seed-json>")
        sys.exit(1)

    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"Seed file not found: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Support either a single test object OR an array of tests
    seeds = raw if isinstance(raw, list) else [raw]

    # Create tables if needed
    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(app_engine, expire_on_commit=False)
    async with Session() as session:
        try:
            async with session.begin():
                for s in seeds:
                    payload = validate_payload(s)
                    test_int_id, test_code = await insert_test(session, payload)
                    print(f"✅ Imported '{payload.title}' (id={test_int_id}, testId={test_code}) with {len(payload.questions)} questions.")
            # session is committed by exiting the transaction block
        finally:
            # ensure connections are closed before the loop ends
            await app_engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
