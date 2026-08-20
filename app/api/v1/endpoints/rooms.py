import random
import string
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.models.room import RoomSession, RoomStatus
from app.schemas.room_schema import RoomCreate, RoomResponse, RoomStartRequest

from app.services.room_service import start_room, force_submit_room
from app.services.exam_service import submit_exam

router = APIRouter()

def generate_room_pin(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(room_in: RoomCreate, db: AsyncSession = Depends(get_db)):
    while True:
        pin = generate_room_pin()
        stmt = select(RoomSession).where(RoomSession.room_pin == pin, RoomSession.status != RoomStatus.COMPLETED)
        if not (await db.execute(stmt)).scalars().first():
            break
            
    db_room = RoomSession(
        exam_id=room_in.exam_id,
        proctor_id=room_in.proctor_id,
        room_pin=pin,
        status=RoomStatus.PENDING
    )
    db.add(db_room)
    await db.commit()
    await db.refresh(db_room)
    return db_room

@router.post("/start", response_model=RoomResponse)
async def start_exam_room_endpoint(req: RoomStartRequest, db: AsyncSession = Depends(get_db)):
    """API Kích hoạt Phòng - Ủy thác Logic xuống tầng Services"""
    try:
        room = await start_room(req.room_id, db)
        await db.commit()
        await db.refresh(room)
        return room
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/{room_id}/force-submit", response_model=RoomResponse)
async def force_submit_exam_room_endpoint(room_id: UUID, db: AsyncSession = Depends(get_db)):
    """API Dừng thi Khẩn cấp - Auto nộp cho toàn bộ sinh viên"""
    try:
        room = await force_submit_room(room_id, db)
        await db.commit()
        await db.refresh(room)
        return room
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ---- API Cho Phía Sinh Viên Nộp Bài Thủ Công ---- #
class SubmitRequest(BaseModel):
    student_id: UUID
    answers: Dict[str, Any]

@router.post("/{room_id}/submit")
async def student_submit_exam(
    room_id: UUID, 
    req: SubmitRequest, 
    db: AsyncSession = Depends(get_db)
):
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
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
