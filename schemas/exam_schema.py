from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.exam import QuestionType
from app.models.room import RoomStatus


# --- QUESTION SCHEMAS ---
class QuestionBase(BaseModel):
    content: str
    type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: list[str] | dict | None = None
    points: float = 1.0
    order_index: int = 0


class QuestionCreate(QuestionBase):
    correct_answer: str


class QuestionResponseAdmin(QuestionBase):
    id: str
    exam_id: str
    correct_answer: str
    model_config = ConfigDict(from_attributes=True)


# Schema trả về cho Thí sinh (ẨN correct_answer)
class QuestionResponseStudent(QuestionBase):
    id: str
    exam_id: str
    model_config = ConfigDict(from_attributes=True)


# --- EXAM SCHEMAS ---
class ExamCreate(BaseModel):
    title: str
    description: str | None = None
    duration_minutes: int
    created_by_id: str
    questions: list[QuestionCreate] = []


class ExamResponse(BaseModel):
    id: str
    title: str
    description: str | None
    duration_minutes: int
    created_by_id: str
    created_at: datetime
    questions: list[QuestionResponseAdmin] = []
    model_config = ConfigDict(from_attributes=True)


# --- ROOM SCHEMAS ---
class RoomCreate(BaseModel):
    exam_id: str
    proctor_id: str


class RoomResponse(BaseModel):
    id: str
    exam_id: str
    proctor_id: str
    room_pin: str
    status: RoomStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)