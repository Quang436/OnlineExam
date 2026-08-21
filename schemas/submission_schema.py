from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
from app.models.submission import SubmissionStatus, ViolationType

class SubmissionCreate(BaseModel):
    room_id: UUID
    student_id: UUID
    answers: Dict[str, Any]

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
