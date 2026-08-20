import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PROCTOR = "PROCTOR"
    STUDENT = "STUDENT"

class User(Base):
    """
    Model quản lý người dùng trong hệ thống (Giám thị, Thí sinh, Admin).
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    # Giám thị: Các kỳ thi do người này tạo
    created_exams = relationship("Exam", back_populates="creator")
    # Giám thị: Các phòng thi do người này gác
    room_sessions = relationship("RoomSession", back_populates="proctor")
    # Thí sinh: Các bài thi (Submissions) của sinh viên này
    submissions = relationship("Submission", back_populates="student")
    # Thí sinh: Lịch sử vi phạm
    violations = relationship("ViolationsLog", back_populates="student")
