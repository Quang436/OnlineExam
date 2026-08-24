from fastapi import APIRouter
from app.api.v1.endpoints.exams import router as exams_router
from app.api.v1.endpoints.rooms import router as rooms_router
from app.api.v1.endpoints.submissions import router as submissions_router
from app.api.v1.endpoints.auth import router as auth_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Xác Thực Hệ Thống"])
api_v1_router.include_router(exams_router, prefix="/exams", tags=["Quản lý Đề Thi & Trắc Nghiệm"])
api_v1_router.include_router(rooms_router, prefix="/rooms", tags=["Quản lý Phiên Gác Thi (Phòng)"])
api_v1_router.include_router(submissions_router, prefix="/submissions", tags=["Chấm Điểm & Lịch Sử Vi Phạm"])