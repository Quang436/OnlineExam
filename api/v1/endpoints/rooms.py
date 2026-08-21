import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.models.exam import Exam
from app.models.room import RoomSession, RoomStatus
from app.schemas.exam_schema import QuestionResponseStudent, RoomCreate, RoomResponse
from app.schemas.room_schema import RoomStartRequest
from app.services.room_service import start_room, force_submit_room
from app.services.exam_service import submit_exam

router = APIRouter()


def generate_pin(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(room_in: RoomCreate, db: AsyncSession = Depends(get_db)):
    exam_res = await db.execute(select(Exam).where(Exam.id == room_in.exam_id))
    if not exam_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam ID không tồn tại")

    room = RoomSession(
        exam_id=room_in.exam_id,
        proctor_id=room_in.proctor_id,
        room_pin=generate_pin(),
        status=RoomStatus.PENDING,
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.get("/pin/{pin}", response_model=RoomResponse)
async def get_room_by_pin(pin: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RoomSession).where(RoomSession.room_pin == pin))
    room = res.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Mã phòng không hợp lệ")
    return room


@router.get("/{room_id}/student-questions", response_model=list[QuestionResponseStudent])
async def get_student_questions(room_id: str, db: AsyncSession = Depends(get_db)):
    """Lấy danh sách câu hỏi cho thí sinh (đã ẩn đáp án đúng)."""
    res = await db.execute(select(RoomSession).where(RoomSession.id == room_id))
    room = res.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Phòng thi không tồn tại")

    exam_res = await db.execute(
        select(Exam).options(selectinload(Exam.questions)).where(Exam.id == room.exam_id)
    )
    exam = exam_res.scalar_one_or_none()
    return exam.questions if exam else []


# ---- CÁC API THIẾT YẾU ĐÃ BỊ XÓA (Phục hồi lại) ---- #

@router.post("/start", response_model=RoomResponse)
async def start_exam_room_endpoint(req: RoomStartRequest, db: AsyncSession = Depends(get_db)):
    """Phát lệnh bắt đầu thi - Đẩy giờ và bắn WebSocket Event xuống tất cả sinh viên"""
    try:
        room = await start_room(str(req.room_id), db)
        await db.commit()
        await db.refresh(room)
        return room
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{room_id}/force-submit", response_model=RoomResponse)
async def force_submit_exam_room_endpoint(room_id: str, db: AsyncSession = Depends(get_db)):
    """Cưỡng ép kết thúc bài thi của tất cả sinh viên chưa nộp"""
    try:
        room = await force_submit_room(room_id, db)
        await db.commit()
        await db.refresh(room)
        return room
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

class SubmitRequest(BaseModel):
    student_id: str
    answers: Dict[str, Any]

@router.post("/{room_id}/submit")
async def student_submit_exam(
    room_id: str, 
    req: SubmitRequest, 
    db: AsyncSession = Depends(get_db)
):
    """API giúp sinh viên nộp bài thủ công và thu điểm lập tức"""
    try:
        score = await submit_exam(
            room_id=room_id, 
            student_id=req.student_id, 
            answers=req.answers, 
            db=db
        )
        await db.commit()
        return {"detail": "Nộp bài thành công", "score": score}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))