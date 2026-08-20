from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from uuid import UUID
from app.models.exam import QuestionType

# --- Questions ---
class QuestionBase(BaseModel):
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    content: str
    options: Optional[Dict[str, Any]] = None
    points: float = 1.0
    order_index: int = 0

class QuestionCreate(QuestionBase):
    correct_answer: str

class QuestionResponseAdmin(QuestionBase):
    """Hiển thị đủ thông tin cho Admin/Giám thị"""
    id: UUID
    exam_id: UUID
    correct_answer: str
    
    model_config = ConfigDict(from_attributes=True)

class QuestionResponseStudent(QuestionBase):
    """CẮT BỎ thuộc tính `correct_answer` khi Thí sinh query lấy đề"""
    id: UUID
    exam_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# --- Exams ---
class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int

class ExamCreate(ExamBase):
    questions: List[QuestionCreate] = []

class ExamResponse(ExamBase):
    """Response trả về cho Admin kèm các Option Admin"""
    id: UUID
    created_by_id: UUID
    questions: List[QuestionResponseAdmin] = []
    
    model_config = ConfigDict(from_attributes=True)

class ExamResponseStudent(ExamBase):
    """Response dành riêng cho Thí sinh"""
    id: UUID
    questions: List[QuestionResponseStudent] = []
    
    model_config = ConfigDict(from_attributes=True)
