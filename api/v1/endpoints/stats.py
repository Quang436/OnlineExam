from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.exam import Exam
from app.models.submission import Submission
from app.models.room import RoomSession
from app.models.user import User

router = APIRouter()

@router.get("/system-overview")
async def get_system_overview(db: AsyncSession = Depends(get_db)):
    total_exams = await db.scalar(select(func.count(Exam.id)))
    total_rooms = await db.scalar(select(func.count(RoomSession.id)))
    total_submissions = await db.scalar(select(func.count(Submission.id)))
    total_users = await db.scalar(select(func.count(User.id)))
    
    # recent rooms
    recent_rooms_res = await db.execute(
        select(RoomSession).options(selectinload(RoomSession.exam)).order_by(RoomSession.created_at.desc()).limit(10)
    )
    recent_rooms = recent_rooms_res.scalars().all()
    
    return {
        "stats": {
            "exams": total_exams or 0,
            "rooms": total_rooms or 0,
            "submissions": total_submissions or 0,
            "users": total_users or 0
        },
        "recent_rooms": [
            {
                "id": str(r.id), 
                "pin": r.room_pin, 
                "status": r.status.value, 
                "exam_title": r.exam.title if r.exam else "Unknown",
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in recent_rooms
        ]
    }
