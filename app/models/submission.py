import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, JSON, Float, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class SubmissionStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    FORCE_SUBMITTED = "FORCE_SUBMITTED"
    REJECTED = "REJECTED"

class ViolationType(str, enum.Enum):
    TAB_SWITCH = "TAB_SWITCH"
    BLUR = "BLUR"
    RESIZE = "RESIZE"
    COPY_PASTE = "COPY_PASTE"
    MULTIPLE_IPS = "MULTIPLE_IPS"
    DISCONNECTED = "DISCONNECTED"

class Submission(Base):
    """
    Model lưu Bài làm / Tiến độ thi của sinh viên trong một Phòng.
    """
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("room_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Lưu dict {"question_id": "answer"} hỗ trợ auto-save
    answers = Column(JSON, nullable=True, default=dict)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.IN_PROGRESS, nullable=False)
    score = Column(Float, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

    # Chặn một học sinh được tạo nhiều Submission trong 1 phòng thi
    __table_args__ = (
        UniqueConstraint("room_id", "student_id", name="uix_room_student_submission"),
    )

    # --- Relationships ---
    room = relationship("RoomSession", back_populates="submissions")
    student = relationship("User", back_populates="submissions")


class ViolationsLog(Base):
    """
    Model lưu Lịch sử vi phạm / Event Log của sinh viên gửi qua WebSocket.
    """
    __tablename__ = "violations_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("room_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    violation_type = Column(Enum(ViolationType), nullable=False)
    
    # Thông tin thêm (ví dụ: duration mất tiêu điểm, số giây rớt mạng)
    evidence_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Tối ưu hóa truy vấn khi giám thị join phòng để fetch lại các violation cũ
    __table_args__ = (
        Index("idx_room_student_violation", "room_id", "student_id", "timestamp"),
    )

    # --- Relationships ---
    room = relationship("RoomSession", back_populates="violations")
    student = relationship("User", back_populates="violations")
