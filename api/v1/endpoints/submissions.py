from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.models.room import RoomSession
from app.models.user import User
from app.models.submission import Submission, ViolationsLog, ViolationType
from app.schemas.submission_schema import (
    SubmissionCreate, 
    SubmissionResponse, 
    ViolationLogResponse, 
    ViolationLogDetailResponse, 
    ViolationStatsResponse
)
from app.services.exam_service import submit_exam

router = APIRouter()


@router.post("/submit", response_model=SubmissionResponse)
async def submit_student_exam(req: SubmissionCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Gọi tầng Service để chấm điểm khép kín
        score, detailed_results = await submit_exam(
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
        
        return SubmissionResponse(
            id=submission.id,
            room_id=submission.room_id,
            student_id=submission.student_id,
            answers=submission.answers,
            status=submission.status,
            score=submission.score,
            started_at=submission.started_at,
            submitted_at=submission.submitted_at,
            detailed_results=detailed_results
        )
        
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


@router.get("/violations/all", response_model=list[ViolationLogDetailResponse])
async def list_all_violations(
    room_id: Optional[UUID] = Query(None, description="Lọc theo phòng thi"),
    student_id: Optional[UUID] = Query(None, description="Lọc theo thí sinh"),
    violation_type: Optional[ViolationType] = Query(None, description="Lọc theo loại vi phạm"),
    search: Optional[str] = Query(None, description="Tìm theo tên thí sinh, username, mã PIN phòng"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Admin lấy toàn bộ log vi phạm trong hệ thống với các bộ lọc chi tiết"""
    query = (
        select(ViolationsLog)
        .options(
            selectinload(ViolationsLog.student),
            selectinload(ViolationsLog.room).selectinload(RoomSession.exam)
        )
    )

    if room_id:
        query = query.where(ViolationsLog.room_id == room_id)
    if student_id:
        query = query.where(ViolationsLog.student_id == student_id)
    if violation_type:
        query = query.where(ViolationsLog.violation_type == violation_type)

    query = query.order_by(ViolationsLog.timestamp.desc())
    res = await db.execute(query)
    all_logs = res.scalars().all()

    if search:
        s = search.strip().lower()
        filtered = []
        for l in all_logs:
            s_name = l.student.full_name.lower() if l.student else ""
            s_user = l.student.username.lower() if l.student else ""
            r_pin = l.room.room_pin.lower() if l.room else ""
            e_title = l.room.exam.title.lower() if (l.room and l.room.exam) else ""
            if s in s_name or s in s_user or s in r_pin or s in e_title:
                filtered.append(l)
        all_logs = filtered

    paginated_logs = all_logs[offset : offset + limit]
    
    result = []
    for l in paginated_logs:
        result.append(ViolationLogDetailResponse(
            id=l.id,
            room_id=l.room_id,
            room_pin=l.room.room_pin if l.room else "N/A",
            exam_title=l.room.exam.title if (l.room and l.room.exam) else "N/A",
            student_id=l.student_id,
            student_name=l.student.full_name if l.student else "Chưa xác định",
            student_username=l.student.username if l.student else "",
            violation_type=l.violation_type,
            evidence_metadata=l.evidence_metadata,
            timestamp=l.timestamp
        ))
    return result


@router.get("/violations/stats", response_model=ViolationStatsResponse)
async def get_violation_stats(db: AsyncSession = Depends(get_db)):
    """Thống kê tổng quan vi phạm: số lượng, phân loại vi phạm, top thí sinh vi phạm"""
    total_violations = await db.scalar(select(func.count(ViolationsLog.id))) or 0

    # Phân loại theo violation_type
    by_type_res = await db.execute(
        select(ViolationsLog.violation_type, func.count(ViolationsLog.id))
        .group_by(ViolationsLog.violation_type)
    )
    by_type = {str(row[0].value if hasattr(row[0], 'value') else row[0]): row[1] for row in by_type_res.all()}

    # Top thí sinh vi phạm nhiều nhất
    top_violators_res = await db.execute(
        select(ViolationsLog.student_id, func.count(ViolationsLog.id).label("cnt"))
        .group_by(ViolationsLog.student_id)
        .order_by(desc("cnt"))
        .limit(5)
    )
    top_rows = top_violators_res.all()
    top_violators = []
    if top_rows:
        student_ids = [r[0] for r in top_rows]
        users_res = await db.execute(select(User).where(User.id.in_(student_ids)))
        users_map = {u.id: u for u in users_res.scalars().all()}

        for s_id, cnt in top_rows:
            u = users_map.get(s_id)
            top_violators.append({
                "student_id": str(s_id),
                "student_name": u.full_name if u else "Unknown",
                "student_username": u.username if u else "",
                "violation_count": cnt
            })

    return ViolationStatsResponse(
        total_violations=total_violations,
        by_type=by_type,
        top_violators=top_violators
    )


@router.delete("/violations/{violation_id}")
async def delete_violation(violation_id: UUID, db: AsyncSession = Depends(get_db)):
    """Xóa một bản ghi log vi phạm"""
    res = await db.execute(select(ViolationsLog).where(ViolationsLog.id == violation_id))
    log = res.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Không tìm thấy log vi phạm")
    
    await db.delete(log)
    await db.commit()
    return {"detail": "Đã xóa log vi phạm thành công"}


@router.delete("/violations/clear/all")
async def clear_all_violations(
    room_id: Optional[UUID] = Query(None, description="Tùy chọn: Chỉ xóa vi phạm của một phòng"),
    db: AsyncSession = Depends(get_db)
):
    """Xóa toàn bộ log vi phạm (hoặc theo phòng thi)"""
    stmt = delete(ViolationsLog)
    if room_id:
        stmt = stmt.where(ViolationsLog.room_id == room_id)
    await db.execute(stmt)
    await db.commit()
    return {"detail": "Đã dọn dẹp log vi phạm thành công"}

