from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.schemas.submission_schema import SubmissionCreate, SubmissionResponse, ViolationLogResponse
from app.services.exam_service import submit_exam
from app.models.submission import Submission, ViolationsLog

router = APIRouter()

@router.post("/submit", response_model=SubmissionResponse)
async def submit_student_exam(req: SubmissionCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Gọi tầng Service để chấm điểm khép kín
        score = await submit_exam(
            room_id=str(req.room_id), 
            student_id=str(req.student_id), 
            answers=req.answers, 
            db=db
        )
        await db.commit()
        
        # Load lại Object từ Database để Parse qua SubmissionResponse
        stmt = select(Submission).where(
            Submission.room_id == req.room_id,
            Submission.student_id == req.student_id
        )
        submission = (await db.execute(stmt)).scalars().first()
        return submission
        
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/room/{room_id}", response_model=list[SubmissionResponse])
async def get_room_submissions(room_id: UUID, db: AsyncSession = Depends(get_db)):
    """API cho Giám thị xem Bảng Điểm toàn phòng"""
    stmt = select(Submission).where(Submission.room_id == room_id)
    subs = (await db.execute(stmt)).scalars().all()
    return subs


@router.get("/room/{room_id}/violations", response_model=list[ViolationLogResponse])
async def get_room_violations(room_id: UUID, db: AsyncSession = Depends(get_db)):
    """API cho Giám thị xem trích lục Biên Bản Gian Lận"""
    stmt = select(ViolationsLog).where(ViolationsLog.room_id == room_id).order_by(ViolationsLog.timestamp.desc())
    logs = (await db.execute(stmt)).scalars().all()
    return logs
