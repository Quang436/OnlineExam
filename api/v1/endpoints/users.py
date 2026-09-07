from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.room import RoomSession
from app.models.exam import Exam
from app.models.submission import Submission, ViolationsLog
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate, UserPasswordReset, UserDetailResponse

router = APIRouter()

@router.get("/", response_model=List[UserDetailResponse])
async def list_users(
    role: Optional[UserRole] = Query(None, description="Lọc theo vai trò"),
    search: Optional[str] = Query(None, description="Tìm theo họ tên, username, email"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách người dùng với các tiêu chí tìm kiếm và thống kê đi kèm"""
    query = select(User)
    
    if role is not None:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.full_name.ilike(search_pattern),
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    users = res.scalars().all()
    
    if not users:
        return []
    
    user_ids = [u.id for u in users]
    
    # Đếm exams do user tạo
    exams_res = await db.execute(
        select(Exam.created_by_id, func.count(Exam.id))
        .where(Exam.created_by_id.in_(user_ids))
        .group_by(Exam.created_by_id)
    )
    exams_map = dict(exams_res.all())
    
    # Đếm rooms do proctor gác
    rooms_res = await db.execute(
        select(RoomSession.proctor_id, func.count(RoomSession.id))
        .where(RoomSession.proctor_id.in_(user_ids))
        .group_by(RoomSession.proctor_id)
    )
    rooms_map = dict(rooms_res.all())
    
    # Đếm submissions của thí sinh
    subs_res = await db.execute(
        select(Submission.student_id, func.count(Submission.id))
        .where(Submission.student_id.in_(user_ids))
        .group_by(Submission.student_id)
    )
    subs_map = dict(subs_res.all())
    
    # Đếm violations của thí sinh
    viols_res = await db.execute(
        select(ViolationsLog.student_id, func.count(ViolationsLog.id))
        .where(ViolationsLog.student_id.in_(user_ids))
        .group_by(ViolationsLog.student_id)
    )
    viols_map = dict(viols_res.all())
    
    result = []
    for u in users:
        result.append(UserDetailResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            exams_count=exams_map.get(u.id, 0),
            rooms_count=rooms_map.get(u.id, 0),
            submissions_count=subs_map.get(u.id, 0),
            violations_count=viols_map.get(u.id, 0),
        ))
    return result


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Admin tạo tài khoản mới (Giáo viên, Giám thị, Thí sinh hoặc Admin)"""
    stmt = select(User).where((User.username == user_in.username) | (User.email == user_in.email))
    existing_user = (await db.execute(stmt)).scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên đăng nhập hoặc Email đã tồn tại trong hệ thống!"
        )

    user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip().lower(),
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        role=user_in.role,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Lấy thông tin chi tiết một người dùng"""
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    exams_count = await db.scalar(select(func.count(Exam.id)).where(Exam.created_by_id == user_id)) or 0
    rooms_count = await db.scalar(select(func.count(RoomSession.id)).where(RoomSession.proctor_id == user_id)) or 0
    submissions_count = await db.scalar(select(func.count(Submission.id)).where(Submission.student_id == user_id)) or 0
    violations_count = await db.scalar(select(func.count(ViolationsLog.id)).where(ViolationsLog.student_id == user_id)) or 0

    return UserDetailResponse(
        id=u.id,
        username=u.username,
        email=u.email,
        full_name=u.full_name,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at,
        exams_count=exams_count,
        rooms_count=rooms_count,
        submissions_count=submissions_count,
        violations_count=violations_count,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, user_in: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Cập nhật thông tin người dùng (Họ tên, Email, Vai trò, Trạng thái hoạt động)"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if user_in.email is not None and user_in.email.strip().lower() != user.email:
        # Check duplicate email
        check_stmt = select(User).where(User.email == user_in.email.strip().lower(), User.id != user_id)
        if (await db.execute(check_stmt)).scalars().first():
            raise HTTPException(status_code=400, detail="Email này đã được sử dụng bởi tài khoản khác")
        user.email = user_in.email.strip().lower()

    if user_in.full_name is not None:
        user.full_name = user_in.full_name.strip()
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}/reset-password")
async def reset_password(user_id: UUID, req: UserPasswordReset, db: AsyncSession = Depends(get_db)):
    """Admin đặt lại mật khẩu mới cho người dùng"""
    if len(req.new_password.strip()) < 4:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 4 ký tự")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.password_hash = get_password_hash(req.new_password)
    await db.commit()
    return {"detail": f"Đã đặt lại mật khẩu thành công cho tài khoản {user.username}"}


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Xóa tài khoản người dùng và dọn dẹp các dữ liệu liên quan"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # Dọn dẹp các dữ liệu liên quan
    await db.execute(delete(ViolationsLog).where(ViolationsLog.student_id == user_id))
    await db.execute(delete(Submission).where(Submission.student_id == user_id))
    
    # Nếu user là proctor của phòng nào, xóa hoặc hủy phòng đó
    rooms_res = await db.execute(select(RoomSession.id).where(RoomSession.proctor_id == user_id))
    r_ids = rooms_res.scalars().all()
    if r_ids:
        await db.execute(delete(ViolationsLog).where(ViolationsLog.room_id.in_(r_ids)))
        await db.execute(delete(Submission).where(Submission.room_id.in_(r_ids)))
        await db.execute(delete(RoomSession).where(RoomSession.id.in_(r_ids)))

    await db.delete(user)
    await db.commit()
    return {"detail": f"Đã xóa thành công tài khoản {user.username}"}
