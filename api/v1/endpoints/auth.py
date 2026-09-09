from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.schemas.user_schema import (
    UserCreate, 
    UserResponse, 
    Token, 
    StudentLoginRequest, 
    StudentLoginResponse, 
    SampleStudentItem
)
from typing import List
from sqlalchemy import func

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    stmt = select(User).where((User.username == user_in.username) | (User.email == user_in.email))
    existing_user = (await db.execute(stmt)).scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username hoặc Email đã tồn tại!")

    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/student-login", response_model=StudentLoginResponse)
async def student_login(req: StudentLoginRequest, db: AsyncSession = Depends(get_db)):
    """Đăng nhập dành riêng cho sinh viên bằng Mã sinh viên (username) và Mật khẩu"""
    code = req.student_code.strip().lower()
    stmt = select(User).where(func.lower(User.username) == code)
    user = (await db.execute(stmt)).scalars().first()
    
    if not user:
        stmt_email = select(User).where(func.lower(User.email) == code)
        user = (await db.execute(stmt_email)).scalars().first()
        
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã sinh viên hoặc mật khẩu không chính xác!"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản sinh viên đã bị khóa. Vui lòng liên hệ Giám thị hoặc Admin!"
        )
        
    access_token = create_access_token(subject=user.id, role=user.role)
    return StudentLoginResponse(
        access_token=access_token,
        token_type="bearer",
        student=user
    )

@router.get("/sample-students", response_model=List[SampleStudentItem])
async def get_sample_students(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách tài khoản sinh viên mẫu có sẵn để tiện test đăng nhập nhanh"""
    stmt = select(User).where(User.role == UserRole.STUDENT).order_by(User.username.asc()).limit(10)
    students = (await db.execute(stmt)).scalars().all()
    
    return [
        SampleStudentItem(
            student_code=s.username,
            full_name=s.full_name,
            email=s.email,
            default_password="123456"
        ) for s in students
    ]

@router.post("/token", response_model=Token)
async def login_access_token(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    uname = form_data.username.strip().lower()
    stmt = select(User).where(func.lower(User.username) == uname)
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        stmt_email = select(User).where(func.lower(User.email) == uname)
        user = (await db.execute(stmt_email)).scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản đã bị cấm")
        
    access_token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
