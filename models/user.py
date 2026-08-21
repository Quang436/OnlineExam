import enum
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PROCTOR = "PROCTOR"
    STUDENT = "STUDENT"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    created_exams: Mapped[List["Exam"]] = relationship(back_populates="creator")
    room_sessions: Mapped[List["RoomSession"]] = relationship(back_populates="proctor")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="student")
    violations: Mapped[List["ViolationsLog"]] = relationship(back_populates="student")