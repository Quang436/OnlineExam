from app.core.database import Base
from app.models.user import User, UserRole
from app.models.exam import Exam, Question, QuestionType
from app.models.room import RoomSession, RoomStatus
from app.models.submission import Submission, SubmissionStatus, ViolationsLog, ViolationType

# Import tất cả Models tại đây để Alembic dễ dàng phát hiện khi auto-generate migrations
__all__ = [
    "Base", 
    "User", "UserRole", 
    "Exam", "Question", "QuestionType", 
    "RoomSession", "RoomStatus", 
    "Submission", "SubmissionStatus", 
    "ViolationsLog", "ViolationType"
]
