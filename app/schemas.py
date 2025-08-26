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
