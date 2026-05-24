"""Wrong Answer Book API routes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from core.database import get_session
from core.models import Question, WrongAnswer

router = APIRouter(prefix="/api/wrongbook", tags=["wrongbook"])


class ReviewData(BaseModel):
    quality: int = 3  # 0-5 SM-2 quality score


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def _sm2_update(wa: WrongAnswer, quality: int) -> None:
    """SM-2 spaced repetition algorithm."""
    if quality >= 3:
        if wa.repetitions == 0:
            wa.interval_days = 1
        elif wa.repetitions == 1:
            wa.interval_days = 6
        else:
            wa.interval_days = round(wa.interval_days * wa.ease_factor)
        wa.repetitions += 1
    else:
        wa.repetitions = 0
        wa.interval_days = 1

    wa.ease_factor = max(1.3, wa.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    wa.mastery_level = min(100, wa.repetitions * 20 + quality * 5)
    wa.next_review = datetime.now(timezone.utc) + timedelta(days=wa.interval_days)


@router.get("")
def list_wrong_answers(
    subject_id: int | None = None,
    due_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(WrongAnswer)
    if subject_id is not None:
        query = query.join(Question).filter(Question.subject_id == subject_id)
    if due_only:
        query = query.filter(WrongAnswer.next_review <= datetime.now(timezone.utc))

    total = query.count()
    items = query.order_by(WrongAnswer.next_review.asc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": wa.id,
                "question_id": wa.question_id,
                "stem": wa.question.stem[:200] if wa.question else "",
                "type": wa.question.type if wa.question else "",
                "subject_name": wa.question.subject.name if wa.question and wa.question.subject else "",
                "user_answer": wa.user_answer,
                "correct_answer": wa.question.answer if wa.question else "",
                "explanation": wa.question.explanation if wa.question else "",
                "mastery_level": wa.mastery_level,
                "review_count": wa.review_count,
                "next_review": wa.next_review.isoformat(),
                "answered_at": wa.answered_at.isoformat(),
                "notes": wa.notes,
            }
            for wa in items
        ],
    }


@router.post("/{wa_id}/review")
def review_wrong_answer(wa_id: int, data: ReviewData = None, db: Session = Depends(get_db)):
    wa = db.query(WrongAnswer).filter(WrongAnswer.id == wa_id).first()
    if not wa:
        return {"error": "Wrong answer not found"}, 404

    quality = data.quality if data else 3
    _sm2_update(wa, quality)
    wa.review_count += 1
    db.commit()
    return {
        "id": wa.id,
        "mastery_level": wa.mastery_level,
        "next_review": wa.next_review.isoformat(),
        "interval_days": wa.interval_days,
    }


@router.delete("/{wa_id}")
def delete_wrong_answer(wa_id: int, db: Session = Depends(get_db)):
    wa = db.query(WrongAnswer).filter(WrongAnswer.id == wa_id).first()
    if not wa:
        return {"error": "Wrong answer not found"}, 404
    db.delete(wa)
    db.commit()
    return {"ok": True}


@router.get("/stats")
def wrongbook_stats(db: Session = Depends(get_db)):
    total = db.query(WrongAnswer).count()
    due = db.query(WrongAnswer).filter(
        WrongAnswer.next_review <= datetime.now(timezone.utc)
    ).count()
    by_subject = db.execute(
        "SELECT s.name, COUNT(*) as cnt FROM wrong_answers wa "
        "JOIN questions q ON q.id = wa.question_id "
        "JOIN subjects s ON s.id = q.subject_id "
        "GROUP BY s.name"
    ).fetchall()

    return {
        "total": total,
        "due_for_review": due,
        "by_subject": [{"subject": r[0], "count": r[1]} for r in by_subject],
    }
