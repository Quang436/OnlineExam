import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class RoomStatus(str, enum.Enum):
    PENDING = "PENDING"       # Phòng đang chờ thí sinh vào
    ACTIVE = "ACTIVE"         # Đang trong thời gian thi
    COMPLETED = "COMPLETED"   # Đã kết thúc
    CANCELLED = "CANCELLED"   # Bị hủy bỏ

class RoomSession(Base):
    """
    Model quản lý Phòng thi thực tế (Room).
    """
    __tablename__ = "room_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), index=True, nullable=False)
    proctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    
    room_pin = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.PENDING, nullable=False)
    
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    exam = relationship("Exam", back_populates="rooms")
    proctor = relationship("User", back_populates="room_sessions")
    submissions = relationship("Submission", back_populates="room")
    violations = relationship("ViolationsLog", back_populates="room")
