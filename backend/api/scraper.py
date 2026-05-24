"""Scraper management API routes."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_session
from core.models import KnowledgePoint, Question, Subject

router = APIRouter(prefix="/api/scraper", tags=["scraper"])


class ScrapeRequest(BaseModel):
    subject_code: str | None = None


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.post("/trigger")
def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger a scrape task in the background."""
    from scraper.registry import run_scrape
    from services.explanation import annotate_question_with_ai

    questions = run_scrape(req.subject_code)
    saved = 0

    for q in questions:
        subj = db.query(Subject).filter(Subject.code == q.subject_code).first()
        if not subj:
            continue

        existing = db.query(Question).filter(
            Question.stem == q.stem,
            Question.subject_id == subj.id,
        ).first()
        if existing:
            continue

        annotated = annotate_question_with_ai({
            "subject_name": subj.name,
            "type": q.type,
            "stem": q.stem,
            "options": q.options,
            "answer": q.answer,
        })

        question = Question(
            subject_id=subj.id,
            type=q.type,
            stem=q.stem,
            options=q.options,
            answer=q.answer,
            explanation=annotated.get("explanation", q.explanation),
            difficulty=annotated.get("difficulty", q.difficulty),
            source_url=q.source_url,
            source_site=q.source_site or "scraper",
        )
        db.add(question)
        db.flush()

        for kp_name in annotated.get("knowledge_points", []):
            kp = db.query(KnowledgePoint).filter(
                KnowledgePoint.subject_id == subj.id,
                KnowledgePoint.name == kp_name,
            ).first()
            if kp:
                question.knowledge_points.append(kp)

        saved += 1

    db.commit()
    return {"message": f"Scrape completed", "total_fetched": len(questions), "saved": saved}


@router.get("/status")
def scraper_status(db: Session = Depends(get_db)):
    total = db.query(Question).count()
    by_subject = db.execute(
        "SELECT s.name, COUNT(*) FROM questions q "
        "JOIN subjects s ON s.id = q.subject_id "
        "GROUP BY s.name"
    ).fetchall()
    return {
        "total_questions": total,
        "by_subject": [{"subject": r[0], "count": r[1]} for r in by_subject],
    }
