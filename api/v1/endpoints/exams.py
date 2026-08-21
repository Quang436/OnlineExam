from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.exam import Exam, Question
from app.schemas.exam_schema import ExamCreate, ExamResponse

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(exam_in: ExamCreate, db: AsyncSession = Depends(get_db)):
    exam = Exam(
        title=exam_in.title,
        description=exam_in.description,
        duration_minutes=exam_in.duration_minutes,
        created_by_id=exam_in.created_by_id,
    )
    db.add(exam)
    await db.flush()

    for q in exam_in.questions:
        question = Question(
            exam_id=exam.id,
            content=q.content,
            type=q.type,
            options=q.options,
            correct_answer=q.correct_answer,
            points=q.points,
            order_index=q.order_index,
        )
        db.add(question)

    await db.commit()
    
    # Query lại để lấy đầy đủ relationship questions
    result = await db.execute(
        select(Exam).options(selectinload(Exam.questions)).where(Exam.id == exam.id)
    )
    return result.scalar_one()


@router.get("/", response_model=list[ExamResponse])
async def list_exams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exam).options(selectinload(Exam.questions)))
    return result.scalars().all()


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Exam).options(selectinload(Exam.questions)).where(Exam.id == exam_id)
    )
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")
    return exam