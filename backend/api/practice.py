"""Practice API routes — submit answers, get results."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_session
from core.models import Question, WrongAnswer
from services.explanation import generate_explanation

router = APIRouter(prefix="/api/practice", tags=["practice"])


class SubmitAnswer(BaseModel):
    question_id: int
    answer: str


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.post("/submit")
def submit_answer(data: SubmitAnswer, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == data.question_id).first()
    if not q:
        return {"error": "Question not found"}, 404

    correct = q.answer.strip().upper() == data.answer.strip().upper()

    result = {
        "correct": correct,
        "correct_answer": q.answer,
        "your_answer": data.answer,
    }

    if not correct:
        # Generate AI explanation if needed
        explanation = q.explanation
        kp_list = [{"id": kp.id, "name": kp.name} for kp in q.knowledge_points]

        if not explanation:
            ai_result = generate_explanation({
                "subject_name": q.subject.name if q.subject else "",
                "type": q.type,
                "stem": q.stem,
                "options": q.options,
                "answer": q.answer,
            })
            explanation = ai_result.get("explanation", "")
            if ai_result.get("explanation"):
                q.explanation = explanation
                q.difficulty = ai_result.get("difficulty", q.difficulty)
                db.commit()

        # Save to wrong answer book
        wa = db.query(WrongAnswer).filter(
            WrongAnswer.question_id == q.id
        ).first()

        if wa:
            wa.user_answer = data.answer
            wa.answered_at = datetime.now(timezone.utc)
            wa.review_count += 1
        else:
            wa = WrongAnswer(
                question_id=q.id,
                user_answer=data.answer,
                answered_at=datetime.now(timezone.utc),
                review_count=0,
                mastery_level=0,
                next_review=datetime.now(timezone.utc) + timedelta(days=1),
                ease_factor=2.5,
                interval_days=1,
                repetitions=0,
            )
            db.add(wa)
        db.commit()

        result["explanation"] = explanation
        result["knowledge_points"] = kp_list
        result["wrong_answer_id"] = wa.id
    else:
        # Remove from wrong book if previously wrong
        wa = db.query(WrongAnswer).filter(
            WrongAnswer.question_id == q.id
        ).first()
        if wa:
            db.delete(wa)
            db.commit()

    return result


@router.get("/history")
def practice_history(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    """Get recent wrong answers as practice history."""
    query = db.query(WrongAnswer).order_by(WrongAnswer.answered_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": wa.id,
                "question_id": wa.question_id,
                "stem": wa.question.stem[:200],
                "user_answer": wa.user_answer,
                "correct_answer": wa.question.answer,
                "subject_name": wa.question.subject.name if wa.question.subject else "",
                "answered_at": wa.answered_at.isoformat(),
                "mastery_level": wa.mastery_level,
            }
            for wa in items
        ],
    }
