from typing import Dict, Any, Set
from fastapi import WebSocket
from pydantic import BaseModel
import json

class ConnectionManager:
    def __init__(self):
        # Cấu trúc In-Memory chuẩn:
        # { room_id: { "students": { student_id: WebSocket }, "proctors": set(WebSocket) } }
        self.rooms: Dict[str, Dict[str, Any]] = {}

    def _ensure_room_exists(self, room_id: str):
        if room_id not in self.rooms:
            self.rooms[room_id] = {
                "proctors": set(),
                "students": {}
            }

    async def connect_student(self, room_id: str, student_id: str, websocket: WebSocket):
        await websocket.accept()
        self._ensure_room_exists(room_id)
        self.rooms[room_id]["students"][student_id] = websocket
        
        # Khi thí sinh kết nối, Tự động broadcast cho giám thị
        await self.broadcast_to_proctors(room_id, {
            "type": "STUDENT_STATUS_CHANGED",
            "student_id": student_id,
            "status": "ONLINE"
        })

    async def connect_proctor(self, room_id: str, proctor_id: str, websocket: WebSocket):
        await websocket.accept()
        self._ensure_room_exists(room_id)
        self.rooms[room_id]["proctors"].add(websocket)

    async def disconnect(self, room_id: str, client_type: str, identifier: str = None, websocket: WebSocket = None):
        if room_id in self.rooms:
            if client_type == "student" and identifier:
                if identifier in self.rooms[room_id]["students"]:
                    del self.rooms[room_id]["students"][identifier]
                    
                    # Khi thí sinh ngắt kết nối (Rớt mạng/Thoát), Tự động broadcast cho giám thị
                    await self.broadcast_to_proctors(room_id, {
                        "type": "STUDENT_STATUS_CHANGED",
                        "student_id": identifier,
                        "status": "OFFLINE"
                    })
            
            elif client_type == "proctor" and websocket:
                if websocket in self.rooms[room_id]["proctors"]:
                    self.rooms[room_id]["proctors"].remove(websocket)
            
            if not self.rooms[room_id]["students"] and not self.rooms[room_id]["proctors"]:
                del self.rooms[room_id]

    async def send_personal_message(self, message: BaseModel | dict, websocket: WebSocket):
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        await websocket.send_json(payload)

    async def broadcast_to_room(self, room_id: str, message: BaseModel | dict):
        if room_id not in self.rooms:
            return
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        for proctor_ws in self.rooms[room_id]["proctors"]:
            await proctor_ws.send_json(payload)
        for student_ws in self.rooms[room_id]["students"].values():
            await student_ws.send_json(payload)

    async def broadcast_to_proctors(self, room_id: str, message: BaseModel | dict):
        if room_id not in self.rooms:
            return
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        for proctor_ws in self.rooms[room_id]["proctors"]:
            await proctor_ws.send_json(payload)

manager = ConnectionManager()