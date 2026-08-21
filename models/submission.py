import enum
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import String, ForeignKey, DateTime, Enum, JSON, Float, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class SubmissionStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    KICKED = "KICKED"

class ViolationType(str, enum.Enum):
    TAB_SWITCH = "TAB_SWITCH"
    BLUR = "BLUR"
    RESIZE = "RESIZE"
    COPY_PASTE = "COPY_PASTE"
    OFFLINE = "OFFLINE"

class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("room_sessions.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    answers: Mapped[Any | None] = mapped_column(JSON, default=dict)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.IN_PROGRESS)
    score: Mapped[float | None] = mapped_column(Float)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        UniqueConstraint("room_id", "student_id", name="uix_room_student_submission"),
    )

    room: Mapped["RoomSession"] = relationship(back_populates="submissions")
    student: Mapped["User"] = relationship(back_populates="submissions")

class ViolationsLog(Base):
    __tablename__ = "violations_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("room_sessions.id", ondelete="CASCADE"))
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    violation_type: Mapped[ViolationType] = mapped_column(Enum(ViolationType))
    evidence_metadata: Mapped[Any | None] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_room_student_violation", "room_id", "student_id", "timestamp"),
    )

    room: Mapped["RoomSession"] = relationship(back_populates="violations")
    student: Mapped["User"] = relationship(back_populates="violations")