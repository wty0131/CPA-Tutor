"""Knowledge point API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from core.database import get_session
from core.models import KnowledgePoint, Question
from services.knowledge import summarize_knowledge_point

router = APIRouter(prefix="/api/knowledge-points", tags=["knowledge_points"])


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def _kp_to_dict(kp: KnowledgePoint, db: Session) -> dict:
    children = [_kp_to_dict(c, db) for c in kp.children]
    direct_count = db.query(Question).filter(
        Question.knowledge_points.any(KnowledgePoint.id == kp.id)
    ).count()
    child_total = sum(c["question_count"] for c in children)
    return {
        "id": kp.id,
        "subject_id": kp.subject_id,
        "parent_id": kp.parent_id,
        "name": kp.name,
        "level": kp.level,
        "description": kp.description,
        "summary": kp.summary,
        "question_count": direct_count + child_total,
        "children": children,
    }


@router.get("")
def list_knowledge_points(subject_id: int | None = None, parent_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(KnowledgePoint)
    if subject_id is not None:
        query = query.filter(KnowledgePoint.subject_id == subject_id)
    if parent_id is not None:
        query = query.filter(KnowledgePoint.parent_id == parent_id)
    else:
        query = query.filter(KnowledgePoint.parent_id.is_(None))

    kps = query.order_by(KnowledgePoint.id).all()
    return [_kp_to_dict(kp, db) for kp in kps]


@router.get("/{kp_id}")
def get_knowledge_point(kp_id: int, db: Session = Depends(get_db)):
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        return {"error": "Knowledge point not found"}, 404
    questions = db.query(Question).filter(
        Question.knowledge_points.any(KnowledgePoint.id == kp.id)
    ).limit(20).all()
    result = _kp_to_dict(kp, db)
    result["questions"] = [
        {"id": q.id, "stem": q.stem[:200], "type": q.type, "difficulty": q.difficulty}
        for q in questions
    ]
    return result


@router.post("/{kp_id}/summarize")
def trigger_summarize(kp_id: int, db: Session = Depends(get_db)):
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        return {"error": "Knowledge point not found"}, 404
    questions = db.query(Question).filter(
        Question.knowledge_points.any(KnowledgePoint.id == kp.id)
    ).all()
    subject_name = kp.subject.name if kp.subject else ""
    result = summarize_knowledge_point(
        kp.name, subject_name,
        [{"stem": q.stem, "type": q.type} for q in questions],
    )
    kp.summary = result.get("summary", "")
    kp.description = "\n".join(result.get("key_concepts", []))
    db.commit()
    return {**_kp_to_dict(kp, db), "ai_result": result}
