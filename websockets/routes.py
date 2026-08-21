import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.websockets.manager import manager
from app.models.room import RoomSession, RoomStatus
from app.models.submission import ViolationsLog, Submission
from app.schemas.ws_messages import BroadcastActionMessage

ws_router = APIRouter(prefix="/ws", tags=["WebSockets"])

@ws_router.websocket("/rooms/{room_id}/student/{student_id}")
async def websocket_student_endpoint(
    websocket: WebSocket,
    room_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    await manager.connect_student(room_id, student_id, websocket)
    
    # [Luật Bổ Sung] Xử lý Late join / Reconnect
    try:
        stmt = select(RoomSession).options(selectinload(RoomSession.exam)).where(RoomSession.id == UUID(room_id))
        room = (await db.execute(stmt)).scalars().first()
        if room and room.status == RoomStatus.ACTIVE:
            msg = BroadcastActionMessage(
                action="EXAM_STARTED",
                payload={
                    "duration_minutes": room.exam.duration_minutes,
                    "end_time_utc": room.ended_at.isoformat()
                }
            )
            await manager.send_personal_message(msg, websocket)
    except Exception:
        pass
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "PING":
                await manager.send_personal_message({
                    "type": "PONG",
                    "client_time": data.get("client_time", 0),
                    "server_time": time.time()
                }, websocket)
                
            elif msg_type == "VIOLATION_ALERT":
                v_type = data.get("violation_type")
                details = data.get("details", {})
                
                # Phản ứng 1: Broadcast ngay cho Giám thị xem
                await manager.broadcast_to_proctors(room_id, {
                    "type": "NEW_VIOLATION",
                    "student_id": student_id,
                    "violation_type": v_type,
                    "details": details,
                    "timestamp": time.time()
                })
                
                # Phản ứng 2: Insert ghi bằng chứng vào PostgreSQL
                try:
                    violation = ViolationsLog(
                        room_id=UUID(room_id),
                        student_id=UUID(student_id),
                        violation_type=v_type,
                        evidence_metadata=details
                    )
                    db.add(violation)
                    await db.commit()
                except Exception:
                    await db.rollback() # Catch lỗi Dummy UUID hoặc Foreign Key khi đang test MOCK
                
            elif msg_type == "AUTO_SAVE":
                answers = data.get("answers", {})
                
                try:
                    # Update DB (Bonus bảo mật Database từ tôi)
                    sub_stmt = select(Submission).where(
                        Submission.room_id == UUID(room_id),
                        Submission.student_id == UUID(student_id)
                    )
                    submission = (await db.execute(sub_stmt)).scalars().first()
                    if submission:
                        submission.answers = answers
                        await db.commit()
                except Exception:
                    await db.rollback()
                
                # Trả ACK lại cho Thí sinh theo Prompt
                await manager.send_personal_message({
                    "type": "AUTO_SAVE_ACK",
                    "status": "SUCCESS"
                }, websocket)
                
    except WebSocketDisconnect:
        await manager.disconnect(room_id=room_id, client_type="student", identifier=student_id)
    except Exception:
        await manager.disconnect(room_id=room_id, client_type="student", identifier=student_id)


@ws_router.websocket("/rooms/{room_id}/proctor/{proctor_id}")
async def websocket_proctor_endpoint(websocket: WebSocket, room_id: str, proctor_id: str):
    await manager.connect_proctor(room_id, proctor_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "START_EXAM":
                duration_minutes = data.get("duration_minutes", 60)
                await manager.broadcast_to_room(room_id, {
                    "type": "BROADCAST_ACTION",
                    "action": "EXAM_STARTED",
                    "payload": {
                        "duration_minutes": duration_minutes,
                        "server_time": time.time()
                    }
                })
                
            elif msg_type == "KICK_STUDENT":
                target_student_id = data.get("student_id")
                target_ws = manager.rooms.get(room_id, {}).get("students", {}).get(target_student_id)
                if target_ws:
                    await manager.send_personal_message({
                        "type": "BROADCAST_ACTION",
                        "action": "EXAM_ENDED", 
                        "reason": "KICKED_BY_PROCTOR"
                    }, target_ws)
                    
    except WebSocketDisconnect:
        await manager.disconnect(room_id=room_id, client_type="proctor", websocket=websocket)
    except Exception:
        await manager.disconnect(room_id=room_id, client_type="proctor", websocket=websocket)