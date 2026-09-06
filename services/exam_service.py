from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from uuid import UUID
from typing import Dict, Any

from app.models.exam import Exam
from app.models.room import RoomSession
from app.models.submission import Submission, SubmissionStatus, ViolationsLog, ViolationType
from app.schemas.submission_schema import string_to_uuid

async def submit_exam(room_id: str, student_id: str, answers: Dict[str, Any], db: AsyncSession) -> tuple[float, list[dict]]:
    # 1. Parse an toàn Id
    room_uid = string_to_uuid(room_id)
    student_uid = string_to_uuid(student_id)
    
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

    # 4. Thuật toán chấm điểm tự động & đối chiếu chi tiết từng câu
    total_score = 0.0
    detailed_results = []
    
    for idx, q in enumerate(exam.questions, 1):
        q_id_str = str(q.id)
        chosen = answers.get(q_id_str)
        is_correct = False
        if chosen is not None:
            is_correct = (str(q.correct_answer).strip().upper() == str(chosen).strip().upper())
        points_earned = float(q.points) if is_correct else 0.0
        total_score += points_earned
        
        detailed_results.append({
            "order": idx,
            "question_id": q_id_str,
            "content": q.content,
            "options": q.options,
            "student_answer": chosen,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "points": float(q.points),
            "points_earned": points_earned
        })
    
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
        
    return total_score, detailed_results


async def log_violation(room_id: str, student_id: str, violation_type: str, details: Dict[str, Any], db: AsyncSession):
    violation = ViolationsLog(
        room_id=string_to_uuid(room_id),
        student_id=string_to_uuid(student_id),
        violation_type=ViolationType(violation_type),
        evidence_metadata=details,
        timestamp=datetime.utcnow()
    )
    db.add(violation)
    await db.commit()
