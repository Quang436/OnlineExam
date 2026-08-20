from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.room import RoomStatus

class RoomCreate(BaseModel):
    exam_id: UUID
    # Tạm thời truyền trực tiếp ID, sau này sẽ nhúng vào token Auth Middleware
    proctor_id: UUID

class RoomResponse(BaseModel):
    id: UUID
    exam_id: UUID
    proctor_id: UUID
    room_pin: str
    status: RoomStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class RoomStartRequest(BaseModel):
    room_id: UUID
