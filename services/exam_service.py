from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from uuid import UUID
from typing import Dict, Any

from app.models.exam import Exam
from app.models.room import RoomSession
from app.models.submission import Submission, SubmissionStatus, ViolationsLog, ViolationType

async def submit_exam(room_id: str, student_id: str, answers: Dict[str, Any], db: AsyncSession) -> float:
    # 1. Parse an toàn Id
    room_uid = UUID(room_id)
    student_uid = UUID(student_id)
    
    # 2. Check Phòng
    stmt = select(RoomSession).where(RoomSession.id == room_uid)
    room = (await db.execute(stmt)).scalars().first()
    if not room:
        raise ValueError("Phòng thi không tồn tại")

    # 3. Lấy Đề Thi + List Câu hỏi (Auto-grading Data)
    exam_stmt = select(Exam).options(selectinload(Exam.questions)).where(Exam.id == room.exam_id)
    exam = (await db.execute(exam_stmt)).scalars().first()
    if not exam:
        raise ValueError("Đề thi bị lỗi: Không tìm thấy đề")

    # 4. Thuật toán chấm điểm tự động (O(1) Hash Map)
    q_map = {str(q.id): q for q in exam.questions}
    total_score = 0.0
    
    for q_id_str, ans_val in answers.items():
        if q_id_str in q_map:
            correct = q_map[q_id_str].correct_answer
            # So sánh linh hoạt không phân biệt hoa/thường khoảng trắng
            if str(correct).strip().upper() == str(ans_val).strip().upper():
                total_score += float(q_map[q_id_str].points)
    
    # 5. Lưu/Cập nhật trạng thái bài nộp thành SUBMITTED
    sub_stmt = select(Submission).where(
        Submission.room_id == room_uid,
        Submission.student_id == student_uid
    )
    submission = (await db.execute(sub_stmt)).scalars().first()
    
    if not submission:
        submission = Submission(
            room_id=room_uid,
            student_id=student_uid,
            answers=answers,
            status=SubmissionStatus.SUBMITTED,
            score=total_score,
            submitted_at=datetime.utcnow()
        )
        db.add(submission)
    else:
        submission.answers = answers
        submission.status = SubmissionStatus.SUBMITTED
        submission.score = total_score
        submission.submitted_at = datetime.utcnow()
        
    return total_score


async def log_violation(room_id: str, student_id: str, violation_type: str, details: Dict[str, Any], db: AsyncSession):
    violation = ViolationsLog(
        room_id=UUID(room_id),
        student_id=UUID(student_id),
        violation_type=ViolationType(violation_type),
        evidence_metadata=details,
        timestamp=datetime.utcnow()
    )
    db.add(violation)
    await db.commit()
