import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoomStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class RoomSession(Base):
    __tablename__ = "room_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    exam_id: Mapped[str] = mapped_column(String(36), ForeignKey("exams.id"), nullable=False)
    proctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    room_pin: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    status: Mapped[RoomStatus] = mapped_column(Enum(RoomStatus), default=RoomStatus.PENDING)
    
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    exam = relationship("Exam", back_populates="rooms")
    proctor = relationship("User")
    submissions = relationship("Submission", back_populates="room")
    violations = relationship("ViolationsLog", back_populates="room")