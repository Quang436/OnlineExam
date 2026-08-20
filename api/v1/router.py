from fastapi import APIRouter
from app.api.v1.endpoints import exams, rooms

api_router = APIRouter()

api_router.include_router(exams.router, prefix="/exams", tags=["Quản lý Đề Thi & Trắc Nghiệm"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Quản lý Phiên Gác Thi (Phòng)"])
