import time
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.websockets.manager import manager
from app.schemas.ws_messages import (
    PongMessage, 
    ViolationAlertMessage, 
    AutoSaveMessage,
    NewViolationBroadcast
)
from app.models.submission import Submission, ViolationsLog, ViolationType

async def handle_student_message(
    room_id: str, 
    student_id: str, 
    data: dict, 
    websocket: WebSocket,
    db: AsyncSession
):
    """
    Xử lý payload logic gửi lên từ Thí sinh: Heartbeat, Gian lận, Auto-save...
    Phân loại dựa trên trường `type`
    """
    msg_type = data.get("type")
    
    if msg_type == "PING":
        # 1. Trả lời Heartbeat và đồng bộ Thời gian thực
        server_ts = int(time.time())
        pong_msg = PongMessage(server_time=server_ts)
        await manager.send_personal_message(pong_msg, websocket)
        
    elif msg_type == "VIOLATION_ALERT":
        # 2. Xử lý log Gian Lận gửi từ API Trình Duyệt Client
        try:
            violation_msg = ViolationAlertMessage(**data)
            
            # Ghi Database
            db_violation = ViolationsLog(
                room_id=room_id,
                student_id=student_id,
                violation_type=ViolationType(violation_msg.violation_type),
                evidence_data=violation_msg.details
            )
            db.add(db_violation)
            await db.commit()
            
            # Bắn Broadcast WebSocket để thông báo tức thì cho Giám Thị trên View Dashboard
            broadcast_msg = NewViolationBroadcast(
                student_id=student_id,
                violation_type=violation_msg.violation_type,
                details=violation_msg.details
            )
            await manager.broadcast_to_proctors(room_id, broadcast_msg)
        except Exception as e:
            # Ghi Log error file nội bộ ở đây nếu parse message văng lỗi
            print(f"Error handling violation: {e}")

    elif msg_type == "AUTO_SAVE":
        # 3. Handle Auto-save tiến độ bài thi
        try:
            autosave_msg = AutoSaveMessage(**data)
            
            # Cập nhật Draft Submission bằng SQLAlchemy Async
            stmt = select(Submission).where(
                Submission.room_id == room_id, 
                Submission.student_id == student_id
            )
            result = await db.execute(stmt)
            submission = result.scalars().first()
            
            if submission:
                submission.answers = autosave_msg.answers
                # Update modified
                await db.commit()
        except Exception as e:
            print(f"Error handling autosave: {e}")
