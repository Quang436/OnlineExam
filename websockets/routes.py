import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.websockets.manager import manager
from app.websockets.handlers import handle_student_message
from app.schemas.ws_messages import StudentStatusChanged

ws_router = APIRouter(prefix="/ws", tags=["WebSockets"])

@ws_router.websocket("/rooms/{room_id}/student/{student_id}")
async def websocket_student_endpoint(
    websocket: WebSocket,
    room_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    await manager.connect_student(room_id, student_id, websocket)
    
    # Broadcast to Proctor: Student Online
    online_msg = StudentStatusChanged(
        student_id=student_id, 
        status="ONLINE", 
        timestamp=time.time()
    )
    await manager.broadcast_to_proctors(room_id, online_msg)
    
    try:
        while True:
            # Bắt dữ liệu JSON và nén luồng điều hướng xuống Middleware Handlers để gọi Database 
            data = await websocket.receive_json()
            await handle_student_message(room_id, student_id, data, websocket, db)
            
    except WebSocketDisconnect:
        manager.disconnect(room_id=room_id, client_type="student", identifier=student_id)
        # Báo cáo offline
        offline_msg = StudentStatusChanged(
            student_id=student_id, 
            status="OFFLINE", 
            timestamp=time.time()
        )
        await manager.broadcast_to_proctors(room_id, offline_msg)

@ws_router.websocket("/rooms/{room_id}/proctor/{proctor_id}")
async def websocket_proctor_endpoint(websocket: WebSocket, room_id: str, proctor_id: str):
    await manager.connect_proctor(room_id, proctor_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            pass
    except WebSocketDisconnect:
        manager.disconnect(room_id=room_id, client_type="proctor", websocket=websocket)