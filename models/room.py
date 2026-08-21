import enum
import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class RoomStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class RoomSession(Base):
    __tablename__ = "room_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    exam_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exams.id"), index=True)
    proctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    room_pin: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    status: Mapped[RoomStatus] = mapped_column(Enum(RoomStatus), default=RoomStatus.PENDING)
    
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    exam: Mapped["Exam"] = relationship(back_populates="rooms")
    proctor: Mapped["User"] = relationship(back_populates="room_sessions")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="room")
    violations: Mapped[List["ViolationsLog"]] = relationship(back_populates="room")