from typing import Dict, Any, Set
from fastapi import WebSocket
from pydantic import BaseModel

class ConnectionManager:
    """Quản lý WebSocket trung tâm (In-Memory Pub/Sub)"""
    def __init__(self):
        self.active_rooms: Dict[str, Dict[str, Any]] = {}

    def _ensure_room_exists(self, room_id: str):
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = {
                "proctors": set(),
                "students": {}
            }

    async def connect_student(self, room_id: str, student_id: str, websocket: WebSocket):
        await websocket.accept()
        self._ensure_room_exists(room_id)
        self.active_rooms[room_id]["students"][student_id] = websocket

    async def connect_proctor(self, room_id: str, proctor_id: str, websocket: WebSocket):
        await websocket.accept()
        self._ensure_room_exists(room_id)
        self.active_rooms[room_id]["proctors"].add(websocket)

    def disconnect(self, room_id: str, client_type: str, identifier: str = None, websocket: WebSocket = None):
        if room_id in self.active_rooms:
            if client_type == "student" and identifier:
                if identifier in self.active_rooms[room_id]["students"]:
                    del self.active_rooms[room_id]["students"][identifier]
            
            elif client_type == "proctor" and websocket:
                if websocket in self.active_rooms[room_id]["proctors"]:
                    self.active_rooms[room_id]["proctors"].remove(websocket)
            
            if not self.active_rooms[room_id]["students"] and not self.active_rooms[room_id]["proctors"]:
                del self.active_rooms[room_id]

    async def send_personal_message(self, message: BaseModel | dict, websocket: WebSocket):
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        await websocket.send_json(payload)

    async def broadcast_to_room(self, room_id: str, message: BaseModel | dict):
        if room_id not in self.active_rooms:
            return
        
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        for proctor_ws in self.active_rooms[room_id]["proctors"]:
            await proctor_ws.send_json(payload)
        for student_ws in self.active_rooms[room_id]["students"].values():
            await student_ws.send_json(payload)

    async def broadcast_to_proctors(self, room_id: str, message: BaseModel | dict):
        if room_id not in self.active_rooms:
            return
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        for proctor_ws in self.active_rooms[room_id]["proctors"]:
            await proctor_ws.send_json(payload)

manager = ConnectionManager()