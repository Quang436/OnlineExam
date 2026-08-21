import enum
import uuid
from datetime import datetime
from typing import List, Any
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    ESSAY = "ESSAY"

class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    creator: Mapped["User"] = relationship(back_populates="created_exams")
    questions: Mapped[List["Question"]] = relationship(back_populates="exam", cascade="all, delete-orphan")
    rooms: Mapped[List["RoomSession"]] = relationship(back_populates="exam")

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    exam_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"), index=True)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), default=QuestionType.MULTIPLE_CHOICE)
    content: Mapped[str] = mapped_column(Text)
    options: Mapped[Any | None] = mapped_column(JSON) 
    correct_answer: Mapped[str] = mapped_column(String)
    points: Mapped[float] = mapped_column(Float, default=1.0)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    exam: Mapped["Exam"] = relationship(back_populates="questions")