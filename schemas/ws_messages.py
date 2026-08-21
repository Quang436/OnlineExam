from pydantic import BaseModel
from typing import Any, Dict, Optional

class BaseWSMessage(BaseModel):
    type: str

class PingMessage(BaseWSMessage):
    type: str = "PING"
    client_time: int
    
class ViolationAlertMessage(BaseWSMessage):
    type: str = "VIOLATION_ALERT"
    violation_type: str
    details: Optional[Dict[str, Any]] = None

class AutoSaveMessage(BaseWSMessage):
    type: str = "AUTO_SAVE"
    answers: Dict[str, Any]

class PongMessage(BaseWSMessage):
    type: str = "PONG"
    server_time: int

class BroadcastActionMessage(BaseWSMessage):
    type: str = "BROADCAST_ACTION"
    action: str
    payload: Optional[Dict[str, Any]] = None
    
class StudentStatusChanged(BaseWSMessage):
    type: str = "STUDENT_STATUS_CHANGED"
    student_id: str
    status: str 
    timestamp: float

class NewViolationBroadcast(BaseWSMessage):
    type: str = "NEW_VIOLATION"
    student_id: str
    violation_type: str
    details: Optional[Dict[str, Any]] = None