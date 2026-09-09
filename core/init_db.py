from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_password_hash
from app.models.user import User, UserRole

INITIAL_USERS = [
    {
        "username": "admin",
        "full_name": "Quản Trị Viên Hệ Thống",
        "email": "admin@proctor.edu.vn",
        "password": "admin",
        "role": UserRole.ADMIN
    },
    {
        "username": "gv_quang",
        "full_name": "ThS. Nguyễn Văn Quang",
        "email": "gv_quang@proctor.edu.vn",
        "password": "123456",
        "role": UserRole.PROCTOR
    },
    {
        "username": "SV001",
        "full_name": "Nguyễn Văn An",
        "email": "sv001@student.edu.vn",
        "password": "123456",
        "role": UserRole.STUDENT
    },
    {
        "username": "SV002",
        "full_name": "Trần Thị Bình",
        "email": "sv002@student.edu.vn",
        "password": "123456",
        "role": UserRole.STUDENT
    },
    {
        "username": "SV003",
        "full_name": "Lê Hoàng Nam",
        "email": "sv003@student.edu.vn",
        "password": "123456",
        "role": UserRole.STUDENT
    },
    {
        "username": "SV004",
        "full_name": "Phạm Minh Tuấn",
        "email": "sv004@student.edu.vn",
        "password": "123456",
        "role": UserRole.STUDENT
    },
    {
        "username": "SV005",
        "full_name": "Hoàng Thị Mai",
        "email": "sv005@student.edu.vn",
        "password": "123456",
        "role": UserRole.STUDENT
    }
]

async def seed_initial_data(db: AsyncSession):
    """Khởi tạo tài khoản mẫu (Admin, Giáo viên, và Thí sinh) nếu chưa có trong DB"""
    for user_data in INITIAL_USERS:
        # Check by username (case-insensitive)
        stmt = select(User).where(User.username.ilike(user_data["username"]))
        existing = (await db.execute(stmt)).scalars().first()
        
        if not existing:
            new_user = User(
                username=user_data["username"],
                full_name=user_data["full_name"],
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_active=True
            )
            db.add(new_user)
        else:
            # Đảm bảo admin có quyền ADMIN nếu trước đó lỡ tạo PROCTOR
            if user_data["username"] == "admin" and existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
                
    await db.commit()
