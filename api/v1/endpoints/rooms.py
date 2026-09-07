import random
import string
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, field_validator
from uuid import UUID

from app.core.database import get_db
from app.models.exam import Exam
from app.models.room import RoomSession, RoomStatus
from app.models.user import User
from app.models.submission import Submission, ViolationsLog
from app.schemas.exam_schema import QuestionResponseStudent
from app.schemas.room_schema import RoomCreate, RoomResponse, RoomStartRequest, RoomDetailResponse, RoomStudentDetailResponse
from app.schemas.submission_schema import string_to_uuid
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


@router.get("/", response_model=List[RoomDetailResponse])
async def list_all_rooms(
    status: Optional[RoomStatus] = Query(None, description="Lọc theo trạng thái phòng"),
    search: Optional[str] = Query(None, description="Tìm theo PIN, tên đề thi hoặc tên giáo viên"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách tất cả phòng thi cùng thông tin giám thị, đề thi, số thí sinh & vi phạm"""
    query = (
        select(RoomSession)
        .options(selectinload(RoomSession.exam), selectinload(RoomSession.proctor))
    )
    if status is not None:
        query = query.where(RoomSession.status == status)
        
    query = query.order_by(RoomSession.created_at.desc())
    res = await db.execute(query)
    all_rooms = res.scalars().all()
    
    if search:
        s = search.strip().lower()
        filtered = []
        for r in all_rooms:
            pin_match = s in r.room_pin.lower()
            exam_match = r.exam and s in r.exam.title.lower()
            proctor_match = r.proctor and (s in r.proctor.full_name.lower() or s in r.proctor.username.lower())
            if pin_match or exam_match or proctor_match:
                filtered.append(r)
        all_rooms = filtered

    paginated_rooms = all_rooms[offset : offset + limit]
    if not paginated_rooms:
        return []

    room_ids = [r.id for r in paginated_rooms]

    subs_res = await db.execute(
        select(Submission.room_id, func.count(Submission.id))
        .where(Submission.room_id.in_(room_ids))
        .group_by(Submission.room_id)
    )
    subs_map = dict(subs_res.all())

    viols_res = await db.execute(
        select(ViolationsLog.room_id, func.count(ViolationsLog.id))
        .where(ViolationsLog.room_id.in_(room_ids))
        .group_by(ViolationsLog.room_id)
    )
    viols_map = dict(viols_res.all())

    result = []
    for r in paginated_rooms:
        result.append(RoomDetailResponse(
            id=r.id,
            exam_id=r.exam_id,
            exam_title=r.exam.title if r.exam else "Đề thi không xác định",
            exam_duration=r.exam.duration_minutes if r.exam else 60,
            proctor_id=r.proctor_id,
            proctor_name=r.proctor.full_name if r.proctor else (r.proctor.username if r.proctor else "Chưa gán"),
            proctor_email=r.proctor.email if r.proctor else "",
            room_pin=r.room_pin,
            status=r.status,
            started_at=r.started_at,
            ended_at=r.ended_at,
            created_at=r.created_at,
            candidates_count=subs_map.get(r.id, 0),
            violations_count=viols_map.get(r.id, 0)
        ))
    return result


@router.get("/{room_id}/candidates", response_model=List[RoomStudentDetailResponse])
async def get_room_candidates(room_id: UUID, db: AsyncSession = Depends(get_db)):
    """Danh sách chi tiết các thí sinh tham gia phòng thi này"""
    res = await db.execute(
        select(Submission)
        .options(selectinload(Submission.student))
        .where(Submission.room_id == room_id)
        .order_by(Submission.started_at.asc())
    )
    subs = res.scalars().all()
    if not subs:
        return []
        
    student_ids = [s.student_id for s in subs]
    viols_res = await db.execute(
        select(ViolationsLog.student_id, func.count(ViolationsLog.id))
        .where(ViolationsLog.room_id == room_id, ViolationsLog.student_id.in_(student_ids))
        .group_by(ViolationsLog.student_id)
    )
    viols_map = dict(viols_res.all())
    
    result = []
    for s in subs:
        result.append(RoomStudentDetailResponse(
            submission_id=s.id,
            student_id=s.student_id,
            student_name=s.student.full_name if s.student else "Chưa xác định",
            student_username=s.student.username if s.student else "",
            student_email=s.student.email if s.student else "",
            status=s.status.value,
            score=s.score,
            started_at=s.started_at,
            submitted_at=s.submitted_at,
            violations_count=viols_map.get(s.student_id, 0)
        ))
    return result


@router.delete("/{room_id}")
async def delete_room(room_id: UUID, db: AsyncSession = Depends(get_db)):
    """Xóa phòng thi và các dữ liệu bài thi / vi phạm liên quan"""
    res = await db.execute(select(RoomSession).where(RoomSession.id == room_id))
    room = res.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Phòng thi không tồn tại")
    
    await db.execute(delete(ViolationsLog).where(ViolationsLog.room_id == room_id))
    await db.execute(delete(Submission).where(Submission.room_id == room_id))
    await db.delete(room)
    await db.commit()
    return {"detail": f"Đã xóa phòng thi {room.room_pin} thành công"}


@router.get("/pin/{pin}", response_model=RoomResponse)
async def get_room_by_pin(pin: str, db: AsyncSession = Depends(get_db)):

    res = await db.execute(select(RoomSession).where(RoomSession.room_pin == pin))
    room = res.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Mã phòng không hợp lệ")
    return room


@router.get("/exam/{exam_id}/active", response_model=RoomResponse | None)
async def get_active_room_for_exam(exam_id: UUID, db: AsyncSession = Depends(get_db)):
    """Lấy phòng thi đang mở (PENDING hoặc ACTIVE) của một đề thi"""
    stmt = (
        select(RoomSession)
        .where(
            RoomSession.exam_id == exam_id,
            RoomSession.status.in_([RoomStatus.PENDING, RoomStatus.ACTIVE])
        )
        .order_by(RoomSession.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().first()


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room_by_id(room_id: UUID, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RoomSession).where(RoomSession.id == room_id))
    room = res.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Phòng thi không tồn tại")
    return room


@router.get("/{room_id}/student-questions", response_model=list[QuestionResponseStudent])
async def get_student_questions(room_id: UUID, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RoomSession).where(RoomSession.id == room_id))
    room = res.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Phòng thi không tồn tại")

    exam_res = await db.execute(
        select(Exam).options(selectinload(Exam.questions)).where(Exam.id == room.exam_id)
    )
    exam = exam_res.scalar_one_or_none()
    return exam.questions if exam else []


# ---- GIỮ VỮNG CÁC API THIẾT YẾU TỪ BẢN GỐC KẺO BỊ MẤT KẾT NỐI VỚI WEBSOCKET ---- #

@router.post("/start", response_model=RoomResponse)
async def start_exam_room_endpoint(req: RoomStartRequest, db: AsyncSession = Depends(get_db)):
    try:
        room = await start_room(req.room_id, db)
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
async def force_submit_exam_room_endpoint(room_id: UUID, db: AsyncSession = Depends(get_db)):
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
    student_id: UUID
    answers: Dict[str, Any]

    @field_validator("student_id", mode="before")
    @classmethod
    def validate_student_id(cls, v):
        return string_to_uuid(v)

@router.post("/{room_id}/submit")
async def student_submit_exam(
    room_id: UUID, 
    req: SubmitRequest, 
    db: AsyncSession = Depends(get_db)
):
    try:
        score, detailed_results = await submit_exam(
            room_id=str(room_id), 
            student_id=str(req.student_id), 
            answers=req.answers, 
            db=db
        )
        await db.commit()
        return {"detail": "Nộp bài thành công", "score": score, "detailed_results": detailed_results}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))