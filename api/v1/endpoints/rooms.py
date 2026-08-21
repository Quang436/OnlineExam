import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.exam import Exam
from app.models.room import RoomSession, RoomStatus
from app.schemas.exam_schema import QuestionResponseStudent, RoomCreate, RoomResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def generate_pin(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(room_in: RoomCreate, db: AsyncSession = Depends(get_db)):
    # Kiểm tra exam có tồn tại không
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