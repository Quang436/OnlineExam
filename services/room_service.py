import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.models.room import RoomSession, RoomStatus
from app.models.submission import Submission, SubmissionStatus
from app.websockets.manager import manager
from app.schemas.ws_messages import BroadcastActionMessage
from app.services.exam_service import submit_exam


async def start_room(room_id: UUID, db: AsyncSession) -> RoomSession:
    """
    Giám thị MỞ CHẾ ĐỘ THI và kích hoạt trigger WebSocket thông báo đồng loạt.
    """
    stmt = select(RoomSession).options(selectinload(RoomSession.exam)).where(RoomSession.id == room_id)
    room = (await db.execute(stmt)).scalars().first()
    
    if not room:
        raise ValueError("Phòng thi không tồn tại")
    if room.status != RoomStatus.PENDING:
        raise ValueError("Phòng thi không ở trạng thái Chờ (PENDING)")

    # Set Time limits chuẩn xác theo giờ UTC của Server
    now = datetime.datetime.utcnow()
    room.status = RoomStatus.ACTIVE
    room.started_at = now
    
    duration = room.exam.duration_minutes
    room.ended_at = now + datetime.timedelta(minutes=duration)
    
    # Ta dùng db.flush() để SQLAlchemy build SQL trước, còn commit sẽ nằm ở tầng API/Transaction
    await db.flush() 
    
    # Kích hoạt WebSocket Broadcast
    # Hàng ngàn devices đợi màn hình "Waiting room" sẽ ngay lập tức được unblock & load Đề Thi
    msg = BroadcastActionMessage(
        action="EXAM_STARTED",
        payload={
            "duration_minutes": duration,
            "end_time_utc": room.ended_at.isoformat()
        }
    )
    await manager.broadcast_to_room(str(room_id), msg)
    
    return room


async def force_submit_room(room_id: UUID, db: AsyncSession) -> RoomSession:
    """
    Giám thị hoặc CronJob kích hoạt KẾT THÚC THI (Hết giờ/Gian lận diện rộng).
    Quét tất cả thí sinh đang thi dở và tự động chốt bài draft gần nhất!
    """
    stmt = select(RoomSession).where(RoomSession.id == room_id)
    room = (await db.execute(stmt)).scalars().first()
    
    if not room or room.status != RoomStatus.ACTIVE:
        raise ValueError("Phòng thi không tồn tại hoặc không trong trạng thái thi")
        
    # Lọc tất cả sinh viên chưa Submit chủ động
    stmt_subs = select(Submission).where(
        Submission.room_id == room_id,
        Submission.status == SubmissionStatus.IN_PROGRESS
    )
    submissions_in_progress = (await db.execute(stmt_subs)).scalars().all()
    
    # Ứng dụng bản Nháp cuối cùng AUTO_SAVE để cứu vớt điểm cho họ
    for sub in submissions_in_progress:
        await submit_exam(
            room_id=room_id, 
            student_id=sub.student_id, 
            answers=sub.answers or {}, 
            db=db, 
            is_force=True
        )
        
    # Đóng bến đỗ
    room.status = RoomStatus.COMPLETED
    room.ended_at = datetime.datetime.utcnow()
    await db.flush()
    
    # Bắn tín hiệu "Khoá Giao diện làm bài"
    msg = BroadcastActionMessage(
        action="EXAM_ENDED",
        payload={"reason": "FORCE_SUBMIT_BY_SERVER"}
    )
    await manager.broadcast_to_room(str(room_id), msg)
    
    return room
