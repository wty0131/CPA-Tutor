"""Question API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from core.database import get_session
from core.models import KnowledgePoint, Question, Subject
from services.explanation import generate_explanation

router = APIRouter(prefix="/api/questions", tags=["questions"])


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def _question_to_dict(q: Question) -> dict:
    return {
        "id": q.id,
        "subject_id": q.subject_id,
        "subject_name": q.subject.name if q.subject else "",
        "type": q.type,
        "stem": q.stem,
        "options": q.options,
        "answer": q.answer,
        "explanation": q.explanation,
        "difficulty": q.difficulty,
        "source_url": q.source_url,
        "source_site": q.source_site,
        "knowledge_points": [
            {"id": kp.id, "name": kp.name} for kp in q.knowledge_points
        ],
    }


@router.get("")
def list_questions(
    subject_id: int | None = None,
    kp_id: int | None = None,
    difficulty: int | None = None,
    type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Question)

    if subject_id is not None:
        query = query.filter(Question.subject_id == subject_id)
    if kp_id is not None:
        query = query.filter(Question.knowledge_points.any(KnowledgePoint.id == kp_id))
    if difficulty is not None:
        query = query.filter(Question.difficulty == difficulty)
    if type is not None:
        query = query.filter(Question.type == type)

    total = query.count()
    questions = query.order_by(Question.id).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_question_to_dict(q) for q in questions],
    }


@router.get("/{question_id}")
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        return {"error": "Question not found"}, 404
    return _question_to_dict(q)


@router.get("/{question_id}/explanation")
def get_explanation(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        return {"error": "Question not found"}, 404

    if q.explanation and not q.explanation.startswith("AI解析"):
        return {"explanation": q.explanation, "knowledge_points": [_kp_to_simple(kp) for kp in q.knowledge_points]}

    result = generate_explanation({
        "subject_name": q.subject.name if q.subject else "",
        "type": q.type,
        "stem": q.stem,
        "options": q.options,
        "answer": q.answer,
    })

    if result.get("explanation"):
        q.explanation = result["explanation"]
        q.difficulty = result.get("difficulty", q.difficulty)
        # Map new knowledge points
        for kp_name in result.get("knowledge_points", []):
            existing = db.query(KnowledgePoint).filter(
                KnowledgePoint.subject_id == q.subject_id,
                KnowledgePoint.name == kp_name,
            ).first()
            if existing and existing not in q.knowledge_points:
                q.knowledge_points.append(existing)
        db.commit()

    return {"explanation": q.explanation, "knowledge_points": [_kp_to_simple(kp) for kp in q.knowledge_points]}


def _kp_to_simple(kp: KnowledgePoint) -> dict:
    return {"id": kp.id, "name": kp.name}
