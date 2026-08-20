import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    ESSAY = "ESSAY"

class Exam(Base):
    """
    Model quản lý bộ Đề thi.
    """
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    creator = relationship("User", back_populates="created_exams")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    rooms = relationship("RoomSession", back_populates="exam")


class Question(Base):
    """
    Model quản lý Câu hỏi thuộc Đề thi.
    """
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False)
    question_type = Column(Enum(QuestionType), default=QuestionType.MULTIPLE_CHOICE, nullable=False)
    content = Column(Text, nullable=False)
    
    # Lưu dưới dạng Dict/Array JSON (vd: {"A": "Đáp án 1", "B": "Đáp án 2"})
    options = Column(JSON, nullable=True) 
    correct_answer = Column(String, nullable=False)
    points = Column(Float, default=1.0)
    order_index = Column(Integer, default=0)

    # --- Relationships ---
    exam = relationship("Exam", back_populates="questions")
