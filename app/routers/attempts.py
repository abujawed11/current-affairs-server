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
