import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Dict, Any

from app.models.room import RoomSession, RoomStatus
from app.models.exam import Exam
from app.models.submission import Submission, SubmissionStatus

async def submit_exam(
    room_id: UUID,
    student_id: UUID, 
    answers: Dict[str, Any], 
    db: AsyncSession,
    is_force: bool = False
) -> float:
    """
    Xử lý logic nộp bài, phân giải đáp án và tính điểm trực tiếp.
    """
    # 1. Fetch dữ liệu Phòng thi kèm theo Đề thi và Bộ câu hỏi gốc
    stmt_room = (
        select(RoomSession)
        .options(selectinload(RoomSession.exam).selectinload(Exam.questions))
        .where(RoomSession.id == room_id)
    )
    result = await db.execute(stmt_room)
    room = result.scalars().first()
    
    if not room:
        raise ValueError("Phòng thi không tồn tại")
        
    if room.status != RoomStatus.ACTIVE:
        raise ValueError("Phòng thi hiện không hoạt động hoặc đã đóng")
    
    # 2. Logic tự động chấm điểm O(N)
    total_score = 0.0
    # Xây dựng Hash Map id -> Từng object câu hỏi để tra cứu siêu tốc
    q_map = {str(q.id): q for q in room.exam.questions}
    
    for q_id_str, answer_val in answers.items():
        q = q_map.get(q_id_str)
        # So khớp đáp án lựa chọn với đáp án gốc trong Database
        if q and q.correct_answer == answer_val:
            total_score += q.points
            
    # 3. Lấy hoặc Khởi tạo Data Submission (Bài làm)
    stmt_sub = select(Submission).where(
        Submission.room_id == room_id, 
        Submission.student_id == student_id
    )
    result_sub = await db.execute(stmt_sub)
    submission = result_sub.scalars().first()
    
    if not submission:
        submission = Submission(room_id=room_id, student_id=student_id)
        db.add(submission)
        
    if submission.status in [SubmissionStatus.SUBMITTED, SubmissionStatus.FORCE_SUBMITTED]:
        raise ValueError("Bạn đã nộp bài rồi, không thể nộp lại")
        
    # 4. Ghi nhận trạng thái hoàn thành an toàn trước khi commit
    submission.answers = answers
    submission.score = total_score
    submission.status = SubmissionStatus.FORCE_SUBMITTED if is_force else SubmissionStatus.SUBMITTED
    submission.submitted_at = datetime.datetime.utcnow()
    
    return total_score
