from typing import Dict, Any, Set
from fastapi import WebSocket
from pydantic import BaseModel

class ConnectionManager:
    """
    Quản lý tập trung các liên kết WebSocket.
    Duy trì hệ thống theo mô hình Pub/Sub nhẹ trong In-Memory RAM.
    """
    def __init__(self):
        # Trạng thái tổng:
        # {
        #   "room_id": {
        #       "proctors": set([ws1, ws2]),
        #       "students": {"uuid-student": ws3, ...}
        #   }
        # }
        self.active_rooms: Dict[str, Dict[str, Any]] = {}

    def _ensure_room_exists(self, room_id: str):
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = {
                "proctors": set(),
                "students": {}
            }

    async def connect_student(self, room_id: str, student_id: str, websocket: WebSocket):
        """Giúp student join phòng"""
        await websocket.accept()
        self._ensure_room_exists(room_id)
        # Sử dụng dict để chặn duplicate/ghi đè connection cũ nếu sinh viên chuyển qua device khác
        self.active_rooms[room_id]["students"][student_id] = websocket

    async def connect_proctor(self, room_id: str, proctor_id: str, websocket: WebSocket):
        """Giúp giám thị join phòng theo dõi"""
        await websocket.accept()
        self._ensure_room_exists(room_id)
        # Giám thị có thể mở nhiều tab, chúng ta dùng set()
        self.active_rooms[room_id]["proctors"].add(websocket)

    def disconnect(self, room_id: str, client_type: str, identifier: str = None, websocket: WebSocket = None):
        """Dọn dẹp bộ nhớ khi user tắt trình duyệt hoặc mất kết nối mạng"""
        if room_id in self.active_rooms:
            if client_type == "student" and identifier:
                if identifier in self.active_rooms[room_id]["students"]:
                    del self.active_rooms[room_id]["students"][identifier]
            
            elif client_type == "proctor" and websocket:
                if websocket in self.active_rooms[room_id]["proctors"]:
                    self.active_rooms[room_id]["proctors"].remove(websocket)
            
            # Giải phóng RAM nếu phòng hoàn toàn rỗng
            if not self.active_rooms[room_id]["students"] and not self.active_rooms[room_id]["proctors"]:
                del self.active_rooms[room_id]

    # --- Methods dùng để gửi messages --- #

    async def send_personal_message(self, message: BaseModel | dict, websocket: WebSocket):
        """Gửi Direct Message cho 1 WebSocket"""
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        await websocket.send_json(payload)

    async def broadcast_to_room(self, room_id: str, message: BaseModel | dict):
        """Gửi cho tất cả những người trong phòng (Kể cả thí sinh, giám thị)"""
        if room_id not in self.active_rooms:
            return
        
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        
        for proctor_ws in self.active_rooms[room_id]["proctors"]:
            await proctor_ws.send_json(payload)
            
        for student_ws in self.active_rooms[room_id]["students"].values():
            await student_ws.send_json(payload)

    async def broadcast_to_proctors(self, room_id: str, message: BaseModel | dict):
        """Chỉ broadcast cho toàn bộ Giám thị trong một phòng"""
        if room_id not in self.active_rooms:
            return
            
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        
        for proctor_ws in self.active_rooms[room_id]["proctors"]:
            await proctor_ws.send_json(payload)

# Global Instance để gọi tại Routes
manager = ConnectionManager()
