from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.user import UserRole

# Login
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

class StudentLoginRequest(BaseModel):
    student_code: str
    password: str

class StudentLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: "UserResponse"

class SampleStudentItem(BaseModel):
    student_code: str
    full_name: str
    email: str
    default_password: str = "123456"


# User
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.PROCTOR

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserPasswordReset(BaseModel):
    new_password: str

class UserDetailResponse(UserResponse):
    exams_count: int = 0
    rooms_count: int = 0
    submissions_count: int = 0
    violations_count: int = 0

