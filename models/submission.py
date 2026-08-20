import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, JSON, String, UniqueConstraint, func
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
    __table_args__ = (
        UniqueConstraint("room_id", "student_id", name="uq_room_student_submission"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("room_sessions.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)  # Lưu dạng: {"question_id": "A"}
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.IN_PROGRESS)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    room = relationship("RoomSession", back_populates="submissions")
    student = relationship("User", back_populates="submissions")


class ViolationsLog(Base):
    __tablename__ = "violations_log"
    __table_args__ = (
        Index("idx_room_student_timestamp", "room_id", "student_id", "timestamp"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("room_sessions.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    violation_type: Mapped[ViolationType] = mapped_column(Enum(ViolationType), nullable=False)
    evidence_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    room = relationship("RoomSession", back_populates="violations")