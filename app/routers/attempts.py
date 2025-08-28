# from __future__ import annotations
# from datetime import datetime, timezone
# import random
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from ..db import get_db
# from ..models import Test, Question, Option, Attempt, AttemptAnswer
# from ..schemas import AttemptCreateIn, AttemptOut, QuestionOut, QuestionOptionOut, AnswerIn, SubmitIn, ReviewOut, ReviewQuestionOut, ReviewOptionOut
# from ..deps import get_current_user
# from ..services.scoring import compute_score
# from ..schemas import (
#     AttemptCreateIn, AttemptOut, QuestionOut, QuestionOptionOut, AnswerIn,
#     SubmitIn, ReviewOut, ReviewQuestionOut, ReviewOptionOut, AttemptGetOut, QuestionOutWithSelection
# )


# router = APIRouter(prefix="/attempts", tags=["attempts"])

# @router.post("", response_model=AttemptOut)
# async def create_attempt(payload: AttemptCreateIn, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
#     test = await db.get(Test, payload.test_id)
#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     qrows = (await db.execute(select(Question).where(Question.test_id == test.id))).scalars().all()
#     if not qrows:
#         raise HTTPException(status_code=400, detail="No questions in test")

#     # pick/shuffle up to 20
#     random.shuffle(qrows)
#     qrows = qrows[:20]
#     attempt = Attempt(user_id=user.id, test_id=test.id)
#     db.add(attempt)
#     await db.flush()

#     # Maintain order via AttemptAnswer.position, and return options
#     out_questions: list[QuestionOut] = []
#     for idx, q in enumerate(qrows, start=1):
#         db.add(AttemptAnswer(attempt_id=attempt.id, question_id=q.id, position=idx))
#         opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
#         random.shuffle(opts)
#         out_questions.append(QuestionOut(
#             id=q.id, date=q.date, category=q.category, stem=q.stem,
#             options=[QuestionOptionOut(id=o.id, text=o.text) for o in opts]
#         ))

#     await db.commit()
#     return AttemptOut(attempt_id=attempt.id, test_id=test.id, questions=out_questions)

# @router.post("/{attempt_id}/answer")
# async def answer(attempt_id: int, payload: AnswerIn, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
#     # validate attempt belongs to user's test implicitly; (extend with ownership checks if needed)
#     att = await db.get(Attempt, attempt_id)
#     if not att:
#         raise HTTPException(status_code=404, detail="Attempt not found")
#     # validate question in this attempt
#     aa = (await db.execute(select(AttemptAnswer).where(
#         AttemptAnswer.attempt_id == attempt_id,
#         AttemptAnswer.question_id == payload.question_id
#     ))).scalar_one_or_none()
#     if not aa:
#         raise HTTPException(status_code=400, detail="Question not part of this attempt")
#     # validate option belongs to question
#     opt = await db.get(Option, payload.option_id)
#     if not opt or opt.question_id != payload.question_id:
#         raise HTTPException(status_code=400, detail="option_id does not belong to question_id")

#     aa.option_id = opt.id
#     await db.commit()
#     return {"ok": True}

# @router.post("/{attempt_id}/submit")
# async def submit(attempt_id: int, payload: SubmitIn, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
#     att = await db.get(Attempt, attempt_id)
#     if not att:
#         raise HTTPException(status_code=404, detail="Attempt not found")

#     # fetch answers and compute correctness
#     rows = (await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id))).scalars().all()
#     correct_flags: list[bool] = []
#     for r in rows:
#         if r.option_id is None:
#             correct_flags.append(False)
#             r.is_correct = False
#         else:
#             o = await db.get(Option, r.option_id)
#             r.is_correct = bool(o.is_correct)
#             correct_flags.append(bool(o.is_correct))

#     score, total, acc = compute_score(correct_flags)
#     from sqlalchemy import func
#     att.score = score
#     att.total = total
#     att.accuracy_pct = acc
#     att.time_taken_sec = payload.time_taken_sec
#     att.submitted_at = func.now()

#     await db.commit()
#     return {"attempt_id": att.id, "score": score, "total": total, "accuracy_pct": acc}

# @router.get("/{attempt_id}/review", response_model=ReviewOut)
# async def review(attempt_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
#     att = await db.get(Attempt, attempt_id)
#     if not att:
#         raise HTTPException(status_code=404, detail="Attempt not found")

#     # Pull questions in stored order
#     aas = (await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id).order_by(AttemptAnswer.position))).scalars().all()
#     qouts: list[ReviewQuestionOut] = []
#     correct_flags: list[bool] = []

#     for aa in aas:
#         q = await db.get(Question, aa.question_id)
#         opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
#         out_opts = []
#         for o in opts:
#             selected = (aa.option_id == o.id)
#             out_opts.append(ReviewOptionOut(id=o.id, text=o.text, is_correct=bool(o.is_correct), selected=selected))
#         if aa.is_correct is not None:
#             correct_flags.append(bool(aa.is_correct))
#         qouts.append(ReviewQuestionOut(id=q.id, stem=q.stem, explanation=q.explanation, options=out_opts))

#     # If not submitted yet, compute on the fly
#     if att.score is None or att.total is None or att.accuracy_pct is None:
#         score, total, acc = compute_score(correct_flags)
#     else:
#         score, total, acc = att.score, att.total, att.accuracy_pct

#     return ReviewOut(attempt_id=att.id, score=score or 0, total=total or len(aas), accuracy_pct=acc or 0.0, questions=qouts)

# @router.get("/{attempt_id}", response_model=AttemptGetOut)
# async def get_attempt(attempt_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
#     att = await db.get(Attempt, attempt_id)
#     if not att:
#         raise HTTPException(status_code=404, detail="Attempt not found")
#     test = await db.get(Test, att.test_id)
#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     # Pull questions in stored order with selected option (if any)
#     aas = (await db.execute(
#         select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id).order_by(AttemptAnswer.position)
#     )).scalars().all()

#     qouts: list[QuestionOutWithSelection] = []
#     for aa in aas:
#         q = await db.get(Question, aa.question_id)
#         opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
#         # keep options order random per attempt creation; we didn’t persist shuffle,
#         # so we just return all options (order doesn’t matter to resume selection)
#         qouts.append(QuestionOutWithSelection(
#             id=q.id,
#             date=q.date,
#             category=q.category,
#             stem=q.stem,
#             options=[QuestionOptionOut(id=o.id, text=o.text) for o in opts],
#             selected_option_id=aa.option_id
#         ))

#     # ... fetch aas, qouts as you already do ...

#     # Server-side remaining time
#     now_utc = datetime.now(timezone.utc)
#     # If att.started_at is naive, treat as UTC (fallback)
#     started = att.started_at if att.started_at.tzinfo else att.started_at.replace(tzinfo=timezone.utc)
#     elapsed = int((now_utc - started).total_seconds())
#     remaining = max(test.duration_sec - elapsed, 0)

#     return AttemptGetOut(
#         attempt_id=att.id,
#         test_id=att.test_id,
#         duration_sec=test.duration_sec,
#         started_at=att.started_at,
#         remaining_sec=remaining,        # 👈 return authoritative remaining
#         questions=qouts
#     )


# @router.get("/{attempt_id}", response_model=AttemptGetOut)
# async def get_attempt(attempt_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
#     att = await db.get(Attempt, attempt_id)
#     if not att:
#         raise HTTPException(status_code=404, detail="Attempt not found")

#     # fetch test for duration
#     test = await db.get(Test, att.test_id)
#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     # Pull questions in stored order with selected option (if any)
#     aas = (await db.execute(
#         select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id).order_by(AttemptAnswer.position)
#     )).scalars().all()

#     qouts: list[QuestionOutWithSelection] = []
#     for aa in aas:
#         q = await db.get(Question, aa.question_id)
#         opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
#         # keep options order random per attempt creation; we didn’t persist shuffle,
#         # so we just return all options (order doesn’t matter to resume selection)
#         qouts.append(QuestionOutWithSelection(
#             id=q.id,
#             date=q.date,
#             category=q.category,
#             stem=q.stem,
#             options=[QuestionOptionOut(id=o.id, text=o.text) for o in opts],
#             selected_option_id=aa.option_id
#         ))

#     return AttemptGetOut(
#         attempt_id=att.id,
#         test_id=att.test_id,
#         duration_sec=test.duration_sec,
#         started_at=att.started_at,
#         questions=qouts
#     )





# app/routers/attempts.py
# from __future__ import annotations
# from datetime import datetime, timezone
# import random
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from ..db import get_db
# from ..models import Test, Question, Option, Attempt, AttemptAnswer, User
# from ..schemas import (
#     AttemptCreateIn, AttemptOut, QuestionOut, QuestionOptionOut, AnswerIn,
#     SubmitIn, ReviewOut, ReviewQuestionOut, ReviewOptionOut, AttemptGetOut, QuestionOutWithSelection
# )
# from ..deps import get_current_user, get_current_user_jwt  # if you want device header auth here
# from ..services.codes import make_code

# router = APIRouter(prefix="/attempts", tags=["attempts"])

# # -------- helpers to resolve codes -> int ids --------
# async def _get_test_by_code(db: AsyncSession, testId: str) -> Test | None:
#     return (await db.execute(select(Test).where(Test.testId == testId))).scalar_one_or_none()

# async def _get_question_by_code(db: AsyncSession, questionId: str) -> Question | None:
#     return (await db.execute(select(Question).where(Question.questionId == questionId))).scalar_one_or_none()

# async def _get_option_by_code(db: AsyncSession, optionId: str) -> Option | None:
#     return (await db.execute(select(Option).where(Option.optionId == optionId))).scalar_one_or_none()

# async def _get_attempt_by_code(db: AsyncSession, attemptId: str) -> Attempt | None:
#     return (await db.execute(select(Attempt).where(Attempt.attemptId == attemptId))).scalar_one_or_none()

# # -------- create attempt --------
# @router.post("", response_model=AttemptOut)
# async def create_attempt(
#     payload: AttemptCreateIn,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user),
# ):
#     test = await _get_test_by_code(db, payload.testId)
#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     qrows = (await db.execute(select(Question).where(Question.test_id == test.id))).scalars().all()
#     if not qrows:
#         raise HTTPException(status_code=400, detail="No questions in test")

#     random.shuffle(qrows)
#     # qrows = qrows[:20]

#     attempt = Attempt(user_id=user.id, test_id=test.id)
#     db.add(attempt)
#     await db.flush()  # get attempt.id
#     attempt.attemptId = make_code("ATT", attempt.id)

#     # prepare out questions + create AttemptAnswer stubs
#     out_questions: list[QuestionOut] = []
#     for idx, q in enumerate(qrows, start=1):
#         # ensure codes exist (legacy-safe)
#         if not q.questionId:
#             q.questionId = make_code("QUS", q.id)
#         db.add(AttemptAnswer(attempt_id=attempt.id, question_id=q.id, position=idx))

#         opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
#         # ensure option codes exist
#         for o in opts:
#             if not o.optionId:
#                 o.optionId = make_code("OPT", o.id)
#         random.shuffle(opts)

#         out_questions.append(QuestionOut(
#             questionId=q.questionId,
#             date=q.date,
#             category=q.category,
#             stem=q.stem,
#             options=[QuestionOptionOut(optionId=o.optionId, text=o.text) for o in opts],
#         ))

#     await db.commit()
#     return AttemptOut(attemptId=attempt.attemptId, testId=test.testId, questions=out_questions)

# # -------- answer a question --------
# @router.post("/{attemptId}/answer")
# async def answer(
#     attemptId: str,
#     payload: AnswerIn,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user_jwt),  # use JWT consistently
# ):
#     att = await _get_attempt_by_code(db, attemptId)
#     if not att or att.user_id != user.id:
#         raise HTTPException(status_code=404, detail="Attempt not found")

#     # resolve codes to rows
#     q = (await db.execute(select(Question).where(Question.questionId == payload.questionId))).scalar_one_or_none()
#     if not q or q.test_id != att.test_id:
#         raise HTTPException(status_code=400, detail="Invalid questionId")

#     opt = (await db.execute(select(Option).where(
#         Option.optionId == payload.optionId,
#         Option.question_id == q.id
#     ))).scalar_one_or_none()
#     if not opt:
#         raise HTTPException(status_code=400, detail="Invalid optionId for this question")

#     aa = (await db.execute(select(AttemptAnswer).where(
#         AttemptAnswer.attempt_id == att.id,
#         AttemptAnswer.question_id == q.id
#     ))).scalar_one_or_none()
#     if not aa:
#         raise HTTPException(status_code=400, detail="Question not part of this attempt")

#     aa.option_id = opt.id
#     await db.commit()
#     return {"ok": True}

# app/routers/attempts.py
from __future__ import annotations
import logging
from datetime import datetime, timezone
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Test, Question, Option, Attempt, AttemptAnswer, User
from ..schemas import (
    AttemptCreateIn, AttemptOut, QuestionOut, QuestionOptionOut, AnswerIn,
    SubmitIn, ReviewOut, ReviewQuestionOut, ReviewOptionOut, AttemptGetOut, QuestionOutWithSelection
)
from ..deps import get_current_user_jwt
from ..services.codes import make_code
from sqlalchemy import select, func  # Add func here

log = logging.getLogger("app.attempts")
router = APIRouter(prefix="/attempts", tags=["attempts"])

# ---------- helpers ----------
async def _get_test_by_code(db: AsyncSession, testId: str) -> Test | None:
    return (await db.execute(select(Test).where(Test.testId == testId))).scalar_one_or_none()

async def _get_question_by_code(db: AsyncSession, questionId: str) -> Question | None:
    return (await db.execute(select(Question).where(Question.questionId == questionId))).scalar_one_or_none()

async def _get_option_by_code(db: AsyncSession, optionId: str) -> Option | None:
    return (await db.execute(select(Option).where(Option.optionId == optionId))).scalar_one_or_none()

async def _get_attempt_by_code(db: AsyncSession, attemptId: str) -> Attempt | None:
    return (await db.execute(select(Attempt).where(Attempt.attemptId == attemptId))).scalar_one_or_none()

 # ---------- create attempt ----------
# @router.post("", response_model=AttemptOut)
# async def create_attempt(
#       payload: AttemptCreateIn,
#       db: AsyncSession = Depends(get_db),
#       user: User = Depends(get_current_user_jwt),
#   ):
#       log.info("create_attempt: user_id=%s, testId=%s, forceNew=%s",
#                user.id, payload.testId, payload.forceNew)

#       test = await _get_test_by_code(db, payload.testId)
#       if not test:
#           log.warning("create_attempt: test not found testId=%s", payload.testId)
#           raise HTTPException(status_code=404, detail="Test not found")

#       # Check for existing in-progress attempts for this test
#       # Use .first() instead of .scalar_one_or_none() to handle multiple results
#       existing_attempt = (await db.execute(
#           select(Attempt).where(
#               Attempt.user_id == user.id,
#               Attempt.test_id == test.id,
#               Attempt.submitted_at.is_(None)  # Not submitted
#           ).order_by(Attempt.started_at.desc())  # Get most recent if multiple
#       )).first()

#       if existing_attempt:
#           existing_attempt = existing_attempt[0]  # Extract the Attempt object

#       # If forceNew=True (Take Again), delete ALL existing attempts for this test
#       if payload.forceNew:
#           log.info("create_attempt: FORCE NEW - deleting ALL existing attempts for test")

#           # Get all in-progress attempts for this test
#           all_existing = (await db.execute(
#               select(Attempt).where(
#                   Attempt.user_id == user.id,
#                   Attempt.test_id == test.id,
#                   Attempt.submitted_at.is_(None)  # Not submitted
#               )
#           )).scalars().all()

#           # Delete all attempt answers and attempts
#           from sqlalchemy import delete
#           for att in all_existing:
#               await db.execute(
#                   delete(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id)
#               )
#               await db.delete(att)

#           await db.flush()
#           existing_attempt = None

#       # If there's still an existing attempt (Resume case), return it
#       if existing_attempt:
#           log.info("create_attempt: RESUME - returning existing attemptId=%s",
#                    existing_attempt.attemptId)

#           # Get existing questions and answers
#           aas = (await db.execute(
#               select(AttemptAnswer).where(AttemptAnswer.attempt_id == existing_attempt.id)
#               .order_by(AttemptAnswer.position)
#           )).scalars().all()

#           out_questions: list[QuestionOut] = []
#           for aa in aas:
#               q = await db.get(Question, aa.question_id)
#               if not q.questionId:
#                   q.questionId = make_code("QUS", q.id)

#               opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
#               for o in opts:
#                   if not o.optionId:
#                       o.optionId = make_code("OPT", o.id)

#               out_questions.append(QuestionOut(
#                   questionId=q.questionId,
#                   date=q.date,
#                   category=q.category,
#                   stem=q.stem,
#                   options=[QuestionOptionOut(optionId=o.optionId, text=o.text) for o in opts],
#               ))

#           await db.commit()  # Save any generated codes
#           return AttemptOut(
#               attemptId=existing_attempt.attemptId,
#               testId=test.testId,
#               questions=out_questions
#           )

#       # CREATE FRESH ATTEMPT (either first time or forceNew=True)
#       log.info("create_attempt: CREATING FRESH ATTEMPT for testId=%s", payload.testId)

#       qrows = (await db.execute(select(Question).where(Question.test_id == test.id))).scalars().all()
#       if not qrows:
#           raise HTTPException(status_code=400, detail="No questions in test")

#       random.shuffle(qrows)

#       attempt = Attempt(user_id=user.id, test_id=test.id)
#       db.add(attempt)
#       await db.flush()
#       attempt.attemptId = make_code("ATT", attempt.id)

#       log.info("create_attempt: FRESH attempt created attemptId=%s", attempt.attemptId)

#       out_questions: list[QuestionOut] = []
#       for idx, q in enumerate(qrows, start=1):
#           if not q.questionId:
#               q.questionId = make_code("QUS", q.id)
#           db.add(AttemptAnswer(attempt_id=attempt.id, question_id=q.id, position=idx))

#           opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
#           for o in opts:
#               if not o.optionId:
#                   o.optionId = make_code("OPT", o.id)
#           random.shuffle(opts)

#           out_questions.append(QuestionOut(
#               questionId=q.questionId,
#               date=q.date,
#               category=q.category,
#               stem=q.stem,
#               options=[QuestionOptionOut(optionId=o.optionId, text=o.text) for o in opts],
#           ))

#       await db.commit()
#       return AttemptOut(attemptId=attempt.attemptId, testId=test.testId, questions=out_questions)


# ---------- create attempt ----------
@router.post("", response_model=AttemptOut)
async def create_attempt(
      payload: AttemptCreateIn,
      db: AsyncSession = Depends(get_db),
      user: User = Depends(get_current_user_jwt),
  ):
      log.info("create_attempt: user_id=%s, testId=%s, forceNew=%s",
               user.id, payload.testId, payload.forceNew)

      test = await _get_test_by_code(db, payload.testId)
      if not test:
          log.warning("create_attempt: test not found testId=%s", payload.testId)
          raise HTTPException(status_code=404, detail="Test not found")

      # Check for existing in-progress attempts for this test
      existing_attempt = (await db.execute(
          select(Attempt).where(
              Attempt.user_id == user.id,
              Attempt.test_id == test.id,
              Attempt.submitted_at.is_(None)  # Not submitted
          ).order_by(Attempt.started_at.desc())  # Get most recent if multiple
      )).first()

      if existing_attempt:
          existing_attempt = existing_attempt[0]  # Extract the Attempt object

      # If forceNew=True (Take Again), delete ALL existing attempts for this test
      if payload.forceNew:
          log.info("create_attempt: FORCE NEW - deleting ALL existing attempts for test")

          # Get all in-progress attempts for this test
          all_existing = (await db.execute(
              select(Attempt).where(
                  Attempt.user_id == user.id,
                  Attempt.test_id == test.id,
                  Attempt.submitted_at.is_(None)  # Not submitted
              )
          )).scalars().all()

          log.info(f"create_attempt: Found {len(all_existing)} existing attempts to delete")

          # Delete all attempt answers and attempts
          from sqlalchemy import delete
          for att in all_existing:
              # Count answers to delete
              answer_count = await db.scalar(
                  select(func.count()).select_from(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id)
              )
              log.info(f"create_attempt: Deleting {answer_count} answers for attempt {att.attemptId}")

              await db.execute(
                  delete(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id)
              )
              await db.delete(att)

          await db.flush()
          existing_attempt = None
          log.info("create_attempt: Successfully deleted all existing attempts")

      # If there's still an existing attempt (Resume case), return it
      if existing_attempt:
          log.info("create_attempt: RESUME - returning existing attemptId=%s",
                   existing_attempt.attemptId)
          # ... existing resume code ...
          return AttemptOut(...)

      # CREATE FRESH ATTEMPT (either first time or forceNew=True)
      log.info("create_attempt: CREATING FRESH ATTEMPT for testId=%s", payload.testId)

      qrows = (await db.execute(select(Question).where(Question.test_id == test.id))).scalars().all()
      if not qrows:
          raise HTTPException(status_code=400, detail="No questions in test")

      log.info(f"create_attempt: Found {len(qrows)} questions for test")
      random.shuffle(qrows)

      attempt = Attempt(user_id=user.id, test_id=test.id)
      db.add(attempt)
      await db.flush()
      attempt.attemptId = make_code("ATT", attempt.id)

      log.info("create_attempt: FRESH attempt created attemptId=%s", attempt.attemptId)

      out_questions: list[QuestionOut] = []
      for idx, q in enumerate(qrows, start=1):
          if not q.questionId:
              q.questionId = make_code("QUS", q.id)
              log.info(f"create_attempt: Generated questionId {q.questionId} for question {q.id}")

          # Create fresh AttemptAnswer with no selected option
          aa = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, position=idx)
          db.add(aa)
          log.info(f"create_attempt: Created AttemptAnswer for question {q.questionId} at position {idx}")

          opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
          for o in opts:
              if not o.optionId:
                  o.optionId = make_code("OPT", o.id)
          random.shuffle(opts)

          out_questions.append(QuestionOut(
              questionId=q.questionId,
              date=q.date,
              category=q.category,
              stem=q.stem,
              options=[QuestionOptionOut(optionId=o.optionId, text=o.text) for o in opts],
          ))

      await db.commit()
      log.info(f"create_attempt: Created {len(out_questions)} fresh questions for attempt {attempt.attemptId}")
      return AttemptOut(attemptId=attempt.attemptId, testId=test.testId, questions=out_questions)

# ---------- answer ----------
@router.post("/{attemptId}/answer")
async def answer(
    attemptId: str,
    payload: AnswerIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_jwt),
):
    log.info("answer: attemptId=%s user_id=%s q=%s opt=%s",
             attemptId, user.id, payload.questionId, payload.optionId)

    att = await _get_attempt_by_code(db, attemptId)
    if not att:
        log.warning("answer: attempt not found attemptId=%s", attemptId)
        raise HTTPException(status_code=404, detail="Attempt not found")
    if att.user_id != user.id:
        log.warning("answer: forbidden attempt.user_id=%s caller.user_id=%s", att.user_id, user.id)
        raise HTTPException(status_code=403, detail="Not your attempt")

    q = await _get_question_by_code(db, payload.questionId)
    if not q or q.test_id != att.test_id:
        log.warning("answer: invalid questionId=%s for attempt test_id=%s", payload.questionId, att.test_id)
        raise HTTPException(status_code=400, detail="Invalid questionId")

    opt = (await db.execute(
        select(Option).where(Option.optionId == payload.optionId, Option.question_id == q.id)
    )).scalar_one_or_none()
    if not opt:
        log.warning("answer: option not in question optionId=%s questionId=%s", payload.optionId, payload.questionId)
        raise HTTPException(status_code=400, detail="Invalid optionId for this question")

    aa = (await db.execute(select(AttemptAnswer).where(
        AttemptAnswer.attempt_id == att.id,
        AttemptAnswer.question_id == q.id
    ))).scalar_one_or_none()
    if not aa:
        log.warning("answer: question not part of attempt attemptId=%s question_pk=%s", attemptId, q.id)
        raise HTTPException(status_code=400, detail="Question not part of this attempt")

    aa.option_id = opt.id
    await db.commit()
    log.info("answer: saved attemptId=%s question_pk=%s option_pk=%s", attemptId, q.id, opt.id)
    return {"ok": True}

# ---------- submit ----------
# @router.post("/{attemptId}/submit")
# async def submit(
#     attemptId: str,
#     payload: SubmitIn,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user_jwt),
# ):
#     from ..services.scoring import compute_score
#     from sqlalchemy import select, func

#     log.info("submit: attemptId=%s user_id=%s", attemptId, user.id)

#     att = await _get_attempt_by_code(db, attemptId)
#     if not att:
#         raise HTTPException(status_code=404, detail="Attempt not found")
#     if att.user_id != user.id:
#         raise HTTPException(status_code=403, detail="Not your attempt")

#     rows = (await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id))).scalars().all()
#     correct_flags: list[bool] = []
#     for r in rows:
#         if r.option_id is None:
#             correct_flags.append(False)
#             r.is_correct = False
#         else:
#             o = await db.get(Option, r.option_id)
#             r.is_correct = bool(o.is_correct)
#             correct_flags.append(bool(o.is_correct))

#     score, total, acc = compute_score(correct_flags)
#     att.score = score
#     att.total = total
#     att.accuracy_pct = acc
#     att.time_taken_sec = payload.time_taken_sec
#     att.submitted_at = func.now()

#     await db.commit()
#     return {"attemptId": att.attemptId, "score": score, "total": total, "accuracy_pct": acc}


# ---------- submit ----------
@router.post("/{attemptId}/submit")
async def submit(
      attemptId: str,
      payload: SubmitIn,
      db: AsyncSession = Depends(get_db),
      user: User = Depends(get_current_user_jwt),
  ):
      from ..services.scoring import compute_score
      from sqlalchemy import select, func

      log.info("submit: attemptId=%s user_id=%s", attemptId, user.id)

      att = await _get_attempt_by_code(db, attemptId)
      if not att:
          raise HTTPException(status_code=404, detail="Attempt not found")
      if att.user_id != user.id:
          raise HTTPException(status_code=403, detail="Not your attempt")

      rows = (await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id))).scalars().all()

      correct_flags: list[bool] = []
      answered_flags: list[bool] = []

      for r in rows:
          was_attempted = r.option_id is not None
          answered_flags.append(was_attempted)

          if not was_attempted:
              # Unattempted question
              correct_flags.append(False)  # Not correct since not answered
              r.is_correct = None  # Mark as unattempted
          else:
              # Attempted question
              o = await db.get(Option, r.option_id)
              is_correct = bool(o.is_correct)
              correct_flags.append(is_correct)
              r.is_correct = is_correct

      # Use new scoring system with negative marking
      score, total, acc = compute_score(correct_flags, answered_flags)

      att.score = score  # This will now be a float (can be negative)
      att.total = total
      att.accuracy_pct = acc
      att.time_taken_sec = payload.time_taken_sec
      att.submitted_at = func.now()

      await db.commit()
      return {"attemptId": att.attemptId, "score": score, "total": total, "accuracy_pct": acc}

# ---------- review ----------
@router.get("/{attemptId}/review", response_model=ReviewOut)
async def review(
    attemptId: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_jwt),
):
    log.info("review: attemptId=%s user_id=%s", attemptId, user.id)

    att = await _get_attempt_by_code(db, attemptId)
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if att.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your attempt")

    aas = (await db.execute(
        select(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id).order_by(AttemptAnswer.position)
    )).scalars().all()

    qouts: list[ReviewQuestionOut] = []
    correct_flags: list[bool] = []

    for aa in aas:
        q = await db.get(Question, aa.question_id)
        if not q.questionId:
            q.questionId = make_code("QUS", q.id)

        opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
        out_opts = []
        for o in opts:
            if not o.optionId:
                o.optionId = make_code("OPT", o.id)
            selected = (aa.option_id == o.id)
            out_opts.append(ReviewOptionOut(optionId=o.optionId, text=o.text, is_correct=bool(o.is_correct), selected=selected))
        if aa.is_correct is not None:
            correct_flags.append(bool(aa.is_correct))
        qouts.append(ReviewQuestionOut(questionId=q.questionId, stem=q.stem, explanation=q.explanation, options=out_opts))

    # If not submitted yet, compute on the fly
    if att.score is None or att.total is None or att.accuracy_pct is None:
        from ..services.scoring import compute_score
        score, total, acc = compute_score(correct_flags)
    else:
        score, total, acc = att.score, att.total, att.accuracy_pct

    t = await db.get(Test, att.test_id)

    return ReviewOut(
        attemptId=att.attemptId,
        testId=t.testId,  # ← ADD THIS LINE
        score=score or 0,
        total=total or len(aas),
        accuracy_pct=acc or 0.0,
        time_taken_sec=att.time_taken_sec,
        submitted_at=att.submitted_at,
        duration_sec=t.duration_sec if t else None,
        questions=qouts
    )

# ---------- get attempt (resume) ----------
@router.get("/{attemptId}", response_model=AttemptGetOut)
async def get_attempt(
    attemptId: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_jwt),
):
    log.info("get_attempt: attemptId=%s user_id=%s", attemptId, user.id)

    att = await _get_attempt_by_code(db, attemptId)
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if att.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your attempt")

    test = await db.get(Test, att.test_id)
    aas = (await db.execute(
        select(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id).order_by(AttemptAnswer.position)
    )).scalars().all()

    qouts: list[QuestionOutWithSelection] = []
    for aa in aas:
        q = await db.get(Question, aa.question_id)
        if not q.questionId:
            q.questionId = make_code("QUS", q.id)
        opts = (await db.execute(select(Option).where(Option.question_id == q.id))).scalars().all()
        for o in opts:
            if not o.optionId:
                o.optionId = make_code("OPT", o.id)

        selected_code = None
        if aa.option_id is not None:
            sel = await db.get(Option, aa.option_id)
            if sel:
                if not sel.optionId:
                    sel.optionId = make_code("OPT", sel.id)
                selected_code = sel.optionId

        qouts.append(QuestionOutWithSelection(
            questionId=q.questionId,
            date=q.date,
            category=q.category,
            stem=q.stem,
            options=[QuestionOptionOut(optionId=o.optionId, text=o.text) for o in opts],
            selected_option_id=selected_code,
        ))

    now_utc = datetime.now(timezone.utc)
    started = att.started_at if att.started_at.tzinfo else att.started_at.replace(tzinfo=timezone.utc)
    elapsed = int((now_utc - started).total_seconds())
    remaining = max(test.duration_sec - elapsed, 0)

    return AttemptGetOut(
        attemptId=att.attemptId,
        testId=test.testId,
        duration_sec=test.duration_sec,
        started_at=att.started_at,
        remaining_sec=remaining,
        questions=qouts,
    )
