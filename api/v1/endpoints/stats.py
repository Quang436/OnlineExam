from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.exam import Exam
from app.models.submission import Submission, ViolationsLog
from app.models.room import RoomSession, RoomStatus
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/system-overview")
async def get_system_overview(db: AsyncSession = Depends(get_db)):
    total_exams = await db.scalar(select(func.count(Exam.id)))
    total_rooms = await db.scalar(select(func.count(RoomSession.id)))
    total_submissions = await db.scalar(select(func.count(Submission.id)))
    total_users = await db.scalar(select(func.count(User.id)))
    total_violations = await db.scalar(select(func.count(ViolationsLog.id)))

    # User role breakdown
    proctors_count = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.PROCTOR)) or 0
    students_count = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.STUDENT)) or 0
    admins_count = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.ADMIN)) or 0

    # Room status breakdown
    active_rooms = await db.scalar(select(func.count(RoomSession.id)).where(RoomSession.status == RoomStatus.ACTIVE)) or 0
    pending_rooms = await db.scalar(select(func.count(RoomSession.id)).where(RoomSession.status == RoomStatus.PENDING)) or 0
    completed_rooms = await db.scalar(select(func.count(RoomSession.id)).where(RoomSession.status == RoomStatus.COMPLETED)) or 0

    # recent rooms
    recent_rooms_res = await db.execute(
        select(RoomSession).options(selectinload(RoomSession.exam), selectinload(RoomSession.proctor)).order_by(RoomSession.created_at.desc()).limit(10)
    )
    recent_rooms = recent_rooms_res.scalars().all()

    # recent violations
    recent_violations_res = await db.execute(
        select(ViolationsLog)
        .options(
            selectinload(ViolationsLog.student),
            selectinload(ViolationsLog.room).selectinload(RoomSession.exam)
        )
        .order_by(ViolationsLog.timestamp.desc())
        .limit(5)
    )
    recent_violations = recent_violations_res.scalars().all()
    
    return {
        "stats": {
            "exams": total_exams or 0,
            "rooms": total_rooms or 0,
            "submissions": total_submissions or 0,
            "users": total_users or 0,
            "violations": total_violations or 0,
            "proctors": proctors_count,
            "students": students_count,
            "admins": admins_count,
            "active_rooms": active_rooms,
            "pending_rooms": pending_rooms,
            "completed_rooms": completed_rooms
        },
        "recent_rooms": [
            {
                "id": str(r.id), 
                "pin": r.room_pin, 
                "status": r.status.value, 
                "exam_title": r.exam.title if r.exam else "Unknown",
                "proctor_name": r.proctor.full_name if r.proctor else "N/A",
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in recent_rooms
        ],
        "recent_violations": [
            {
                "id": str(v.id),
                "room_pin": v.room.room_pin if v.room else "N/A",
                "exam_title": v.room.exam.title if (v.room and v.room.exam) else "N/A",
                "student_name": v.student.full_name if v.student else "Chưa xác định",
                "violation_type": v.violation_type.value if hasattr(v.violation_type, 'value') else str(v.violation_type),
                "timestamp": v.timestamp.isoformat() if v.timestamp else None,
                "evidence": v.evidence_metadata
            } for v in recent_violations
        ]
    }

