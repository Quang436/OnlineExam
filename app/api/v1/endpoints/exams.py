from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.core.database import get_db
from app.models.exam import Exam, Question
from app.schemas.exam_schema import ExamCreate, ExamResponse, ExamResponseStudent

router = APIRouter()

@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam_in: ExamCreate, 
    proctor_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """
    Giám thị TẠO mới một Đề Thi (kèm danh sách Câu hỏi).
    """
    db_exam = Exam(
        title=exam_in.title,
        description=exam_in.description,
        duration_minutes=exam_in.duration_minutes,
        created_by_id=proctor_id, # Đáng lẽ lấy từ Depends(get_current_user)
    )
    db.add(db_exam)
    await db.flush() # Flush để SQLAlchemy sinh ra UUID ở `db_exam.id` trước khi add Question

    # Tạo đồng loạt bộ câu hỏi
    for q in exam_in.questions:
        db_question = Question(
            exam_id=db_exam.id,
            question_type=q.question_type,
            content=q.content,
            options=q.options,
            correct_answer=q.correct_answer,
            points=q.points,
            order_index=q.order_index
        )
        db.add(db_question)

    await db.commit()
    await db.refresh(db_exam)
    
    # Để Response Models có thể parse list Questions, ta cần query nạp sẵn Relation (Select In Load)
    stmt = select(Exam).options(selectinload(Exam.questions)).where(Exam.id == db_exam.id)
    result = await db.execute(stmt)
    return result.scalars().first()


@router.get("/{exam_id}/student", response_model=ExamResponseStudent)
async def get_exam_for_student(
    exam_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """
    Thí sinh LẤY Đề Thi: 
    Do filter qua Pydantic Model `ExamResponseStudent`, đáp án `correct_answer` tự động bị DROPPED. 
    Không có rủi ro lộ đề qua F12 Network Tab!
    """
    stmt = select(Exam).options(selectinload(Exam.questions)).where(Exam.id == exam_id)
    result = await db.execute(stmt)
    exam = result.scalars().first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy Đề thi")
        
    return exam
