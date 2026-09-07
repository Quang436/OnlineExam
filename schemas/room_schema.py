from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.room import RoomStatus

class RoomCreate(BaseModel):
    exam_id: UUID
    proctor_id: UUID

class RoomResponse(BaseModel):
    id: UUID
    exam_id: UUID
    proctor_id: UUID
    room_pin: str
    status: RoomStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RoomStartRequest(BaseModel):
    room_id: UUID

class RoomDetailResponse(BaseModel):
    id: UUID
    exam_id: UUID
    exam_title: str
    exam_duration: int
    proctor_id: UUID
    proctor_name: str
    proctor_email: str
    room_pin: str
    status: RoomStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    candidates_count: int = 0
    violations_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class RoomStudentDetailResponse(BaseModel):
    submission_id: UUID
    student_id: UUID
    student_name: str
    student_username: str
    student_email: str
    status: str
    score: Optional[float] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None
    violations_count: int = 0

    model_config = ConfigDict(from_attributes=True)

