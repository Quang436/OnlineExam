from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.schemas.user_schema import UserCreate, UserResponse, Token

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

@router.post("/token", response_model=Token)
async def login_access_token(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    stmt = select(User).where(User.username == form_data.username)
    user = (await db.execute(stmt)).scalars().first()
    
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
