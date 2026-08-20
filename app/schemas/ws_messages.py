from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional

# --- Base Schema --- #
class BaseWSMessage(BaseModel):
    """
    Message gốc dùng chung cho mọi payload qua WebSocket.
    Tất cả các tin nhắn trao đổi qua lại giữa Client-Server bắt buộc phải có thuộc tính `type`.
    """
    type: str

# --- Client -> Server Messages --- #
class PingMessage(BaseWSMessage):
    type: str = "PING"
    client_time: int
    
class ViolationAlertMessage(BaseWSMessage):
    """
    Sử dụng khi browser detects hành vi gian lận (Tab switch, lose focus).
    """
    type: str = "VIOLATION_ALERT"
    violation_type: str
    details: Optional[Dict[str, Any]] = None

class AutoSaveMessage(BaseWSMessage):
    """
    Sử dụng để thí sinh tự động lưu bản nháp đáp án định kỳ mà không cần HTTP request.
    """
    type: str = "AUTO_SAVE"
    answers: Dict[str, Any]

# --- Server -> Client Messages --- #
class PongMessage(BaseWSMessage):
    type: str = "PONG"
    server_time: int

class BroadcastActionMessage(BaseWSMessage):
    """
    Dùng để phát lệnh cho toàn phòng thi (Ví dụ: Start, Pause, End exam).
    """
    type: str = "BROADCAST_ACTION"
    action: str
    payload: Optional[Dict[str, Any]] = None
    
# --- Server -> Proctor (Giám sát tức thì) --- #
class StudentStatusChanged(BaseWSMessage):
    """
    Báo giám thị biết có 1 sinh viên rớt mạng / vô mạng.
    """
    type: str = "STUDENT_STATUS_CHANGED"
    student_id: str
    status: str # ONLINE / OFFLINE
    timestamp: float

class NewViolationBroadcast(BaseWSMessage):
    """
    Thông báo real-time khi sinh viên gian lận, dùng để push notification lên Dashboard Admin.
    """
    type: str = "NEW_VIOLATION"
    student_id: str
    violation_type: str
    details: Optional[Dict[str, Any]] = None
