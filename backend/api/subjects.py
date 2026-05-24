"""Subject API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_session
from core.models import Question, Subject, WrongAnswer

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_subjects(db: Session = Depends(get_db)):
    subjects = db.query(Subject).order_by(Subject.code).all()
    result = []
    for s in subjects:
        q_count = db.query(Question).filter(Question.subject_id == s.id).count()
        wa_count = db.query(WrongAnswer).filter(
            WrongAnswer.question.has(Question.subject_id == s.id)
        ).count()
        result.append({
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "description": s.description,
            "question_count": q_count,
            "wrong_count": wa_count,
        })
    return result


@router.get("/{subject_id}")
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    s = db.query(Subject).filter(Subject.id == subject_id).first()
    if not s:
        return {"error": "Subject not found"}, 404
    q_count = db.query(Question).filter(Question.subject_id == s.id).count()
    kp_count = s.knowledge_points
    return {
        "id": s.id,
        "code": s.code,
        "name": s.name,
        "description": s.description,
        "question_count": q_count,
        "knowledge_point_count": len(kp_count),
    }
