import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    ESSAY = "ESSAY"


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creator = relationship("User", back_populates="created_exams")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    rooms = relationship("RoomSession", back_populates="exam")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    exam_id: Mapped[str] = mapped_column(String(36), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), default=QuestionType.MULTIPLE_CHOICE)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | list] = mapped_column(JSON, nullable=True)  # Ví dụ: ["A. ...", "B. ..."] hoặc {"A": "...", "B": "..."}
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    points: Mapped[float] = mapped_column(Float, default=1.0)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    exam = relationship("Exam", back_populates="questions")