from fastapi import APIRouter
from app.api.v1.endpoints.exams import router as exams_router
from app.api.v1.endpoints.rooms import router as rooms_router

api_v1_router = APIRouter()
api_v1_router.include_router(exams_router, prefix="/exams", tags=["Quản lý Đề Thi & Trắc Nghiệm"])
api_v1_router.include_router(rooms_router, prefix="/rooms", tags=["Quản lý Phiên Gác Thi (Phòng)"])