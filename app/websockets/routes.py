import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.websockets.manager import manager
from app.websockets.handlers import handle_student_message
from app.schemas.ws_messages import StudentStatusChanged

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/rooms/{room_id}/student/{student_id}")
async def websocket_student_endpoint(
    websocket: WebSocket,
    room_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint duy trì Connection 2 chiều với Thí sinh.
    Sử dụng URL Parameter để route (sau này nên bọc Middleware xác thực UUID).
    """
    await manager.connect_student(room_id, student_id, websocket)
    
    # Push sự kiện Thông báo tới Giám Thị rằng sinh viên này vừa ONLINE
    online_msg = StudentStatusChanged(
        student_id=student_id, 
        status="ONLINE", 
        timestamp=time.time()
    )
    await manager.broadcast_to_proctors(room_id, online_msg)
    
    try:
        while True:
            # Chờ Event dạng JSON
            data = await websocket.receive_json()
            # Đẩy vào Handler Middleware phân tách Service Logic
            await handle_student_message(room_id, student_id, data, websocket, db)
            
    except WebSocketDisconnect:
        # Trường hợp rớt mạng, close, tắt browser
        manager.disconnect(room_id=room_id, client_type="student", identifier=student_id)
        
        # Báo ngay cho ban giám thị thí sinh bị mất kết nối / OFFLINE
        offline_msg = StudentStatusChanged(
            student_id=student_id, 
            status="OFFLINE", 
            timestamp=time.time()
        )
        await manager.broadcast_to_proctors(room_id, offline_msg)


@router.websocket("/rooms/{room_id}/proctor/{proctor_id}")
async def websocket_proctor_endpoint(
    websocket: WebSocket,
    room_id: str,
    proctor_id: str
):
    """
    Endpoint duy trì Connection nhận cảnh báo vi phạm của Giám Thị.
    Có thể để dashboard mở xuyên suốt không giới hạn time-out kết nối.
    """
    await manager.connect_proctor(room_id, proctor_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            # TODO: Giám thị có quyền phát lệnh (vd: 'START_EXAM', 'KICK_STUDENT')
            # Ở bản MVP có thể bỏ trống, chỉ cần open socket để nhận "broadcast_to_proctors" ở dưới nền
            pass
    except WebSocketDisconnect:
        manager.disconnect(room_id=room_id, client_type="proctor", websocket=websocket)
