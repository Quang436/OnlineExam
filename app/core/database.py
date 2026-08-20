from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Khởi tạo Async Engine cho SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set True để xem log SQL query trong quá trình development
    future=True
)

# Khởi tạo sessionmaker dành cho AsyncSession
async_session_maker = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False, 
    autoflush=False
)

# Class Base để các Models kế thừa
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function phục vụ việc inject AsyncSession vào các API endpoints.
    Đảm bảo session được tạo và đóng đúng vòng đời của request.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
