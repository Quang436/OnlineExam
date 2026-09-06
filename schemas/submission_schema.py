from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, Dict, Optional
from uuid import UUID
import uuid
from datetime import datetime
from app.models.submission import SubmissionStatus, ViolationType

def string_to_uuid(val: Any) -> UUID:
    if isinstance(val, UUID):
        return val
    val_str = str(val).strip()
    try:
        return UUID(val_str)
    except (ValueError, AttributeError):
        # Tự động chuyển đổi chuỗi bất kỳ (như "13", "SV01") thành UUID hợp lệ theo chuẩn namespace
        return uuid.uuid5(uuid.NAMESPACE_DNS, val_str)

class SubmissionCreate(BaseModel):
    room_id: UUID
    student_id: UUID
    answers: Dict[str, Any]

    @field_validator("student_id", mode="before")
    @classmethod
    def convert_student_id(cls, v):
        return string_to_uuid(v)

class SubmissionResponse(BaseModel):
    id: UUID
    room_id: UUID
    student_id: UUID
    answers: Optional[Dict[str, Any]]
    status: SubmissionStatus
    score: Optional[float]
    started_at: datetime
    submitted_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class ViolationLogResponse(BaseModel):
    id: UUID
    room_id: UUID
    student_id: UUID
    violation_type: ViolationType
    evidence_metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
