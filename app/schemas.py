# from __future__ import annotations
# from datetime import datetime, date
# from typing import List, Optional
# from pydantic import BaseModel, Field, EmailStr
# from datetime import datetime  # add

# class TestOut(BaseModel):
#     id: int
#     title: str
#     duration_sec: int

# class TestDetailOut(BaseModel):
#     id: int
#     title: str
#     duration_sec: int
#     question_count: int

# class AttemptCreateIn(BaseModel):
#     test_id: int

# class QuestionOptionOut(BaseModel):
#     id: int
#     text: str

# class QuestionOut(BaseModel):
#     id: int
#     date: date
#     category: str
#     stem: str
#     options: List[QuestionOptionOut]

# class AttemptOut(BaseModel):
#     attempt_id: int
#     test_id: int
#     questions: List[QuestionOut]

# class AnswerIn(BaseModel):
#     question_id: int
#     option_id: int

# class SubmitIn(BaseModel):
#     time_taken_sec: int

# class ReviewOptionOut(BaseModel):
#     id: int
#     text: str
#     is_correct: bool
#     selected: bool

# class ReviewQuestionOut(BaseModel):
#     id: int
#     stem: str
#     explanation: str
#     options: List[ReviewOptionOut]

# class ReviewOut(BaseModel):
#     attempt_id: int
#     score: int
#     total: int
#     accuracy_pct: float
#     questions: List[ReviewQuestionOut]


# class QuestionOutWithSelection(QuestionOut):
#     selected_option_id: int | None = None

# class AttemptGetOut(BaseModel):
#     attempt_id: int
#     test_id: int
#     duration_sec: int
#     started_at: datetime
#     remaining_sec: int            # 👈 add this
#     questions: list[QuestionOutWithSelection]


# # ---------- Auth ----------
# class UserOut(BaseModel):
#     id: int
#     username: str
#     email: EmailStr

# class SignupIn(BaseModel):
#     username: str = Field(min_length=3, max_length=50)
#     email: EmailStr
#     password: str = Field(min_length=6, max_length=128)

# class LoginIn(BaseModel):
#     username: str
#     password: str

# class AuthOut(BaseModel):
#     token: str
#     user: UserOut

# # ---------- /me/attempts ----------
# class AttemptSummary(BaseModel):
#     id: int
#     test_id: int
#     title: str
#     score: int
#     total: int
#     accuracy_pct: float
#     submitted_at: datetime




from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


# =========================
#        TESTS
# =========================

class LastAttemptMini(BaseModel):
    attemptId: str
    accuracy_pct: float



class TestOut(BaseModel):
    testId: str
    title: str
    duration_sec: int
    last_attempt: LastAttemptMini | None = None

    

class TestDetailOut(BaseModel):
    testId: str
    title: str
    duration_sec: int
    question_count: int


# =========================
#        ATTEMPTS
# =========================

class AttemptCreateIn(BaseModel):
    # Previously: test_id: int
    # Now the frontend will send the pretty code:
    testId: str = Field(..., description="e.g. TEST000123")
    forceNew: Optional[bool] = False  # Add this line


class QuestionOptionOut(BaseModel):
    optionId: str
    text: str


class QuestionOut(BaseModel):
    questionId: str
    date: date
    category: str
    stem: str
    options: List[QuestionOptionOut]


class AttemptOut(BaseModel):
    attemptId: str
    testId: str
    questions: List[QuestionOut]


class AnswerIn(BaseModel):
    # Previously: question_id, option_id (ints)
    questionId: str
    optionId: str


class SubmitIn(BaseModel):
    time_taken_sec: int


class ReviewOptionOut(BaseModel):
    optionId: str
    text: str
    is_correct: bool
    selected: bool


class ReviewQuestionOut(BaseModel):
    questionId: str
    stem: str
    explanation: str
    options: List[ReviewOptionOut]


class ReviewOut(BaseModel):
    attemptId: str
    testId: str  # ← ADD THIS LINE
    # score: int
    score: float  # Changed from int to float
    total: int
    accuracy_pct: float
    questions: List[ReviewQuestionOut]
    time_taken_sec: int | None = None
    submitted_at: datetime | None = None
    duration_sec: int | None = None


class QuestionOutWithSelection(QuestionOut):
    selected_option_id: Optional[str] = None  # still expose code


class AttemptGetOut(BaseModel):
    attemptId: str
    testId: str
    duration_sec: int
    started_at: datetime
    remaining_sec: int
    questions: List[QuestionOutWithSelection]


# =========================
#        AUTH / USER
# =========================

class UserOut(BaseModel):
    userId: str
    username: str
    email: EmailStr


class SignupIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


# =========================
#   /me/attempts summary
# =========================

class AttemptSummary(BaseModel):
    attemptId: str
    testId: str
    title: str
    # score: int
    score: float  # Changed from int to float
    total: int
    accuracy_pct: float
    submitted_at: datetime
    time_taken_sec: Optional[int] = None  # Add this line





