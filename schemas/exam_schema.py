from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from app.models.exam import QuestionType

# --- QUESTION SCHEMAS ---
class QuestionBase(BaseModel):
    content: str
    type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: Optional[Any] = None
    points: float = 1.0
    order_index: int = 0

class QuestionCreate(QuestionBase):
    correct_answer: str

class QuestionResponseAdmin(QuestionBase):
    id: UUID
    exam_id: UUID
    correct_answer: str
    model_config = ConfigDict(from_attributes=True)

# Schema trả về cho Thí sinh (Ẩn đáp án đúng để chống gian lận)
class QuestionResponseStudent(QuestionBase):
    id: UUID
    exam_id: UUID
    model_config = ConfigDict(from_attributes=True)


# --- EXAM SCHEMAS ---
class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int

class ExamCreate(ExamBase):
    created_by_id: UUID
    questions: List[QuestionCreate] = []

class ExamResponse(ExamBase):
    id: UUID
    created_by_id: UUID
    created_at: datetime
    questions: List[QuestionResponseAdmin] = []
    model_config = ConfigDict(from_attributes=True)