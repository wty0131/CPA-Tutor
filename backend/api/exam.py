"""Mock exam API routes."""
from __future__ import annotations

import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_session
from core.models import Question, Subject, KnowledgePoint

router = APIRouter(prefix="/api/exam", tags=["exam"])


EXAM_CONFIG = {
    "single_choice": 15,
    "multi_choice": 5,
    "calculation": 5,
}

DIFFICULTY_WEIGHTS = {1: 10, 2: 40, 3: 35, 4: 10, 5: 5}


class SubmitExam(BaseModel):
    answers: dict[str, str]  # {question_id: answer}


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate")
def generate_exam(subject_id: int | None = None, db: Session = Depends(get_db)):
    """Generate a mock exam with proper question type distribution."""
    exam_questions = []

    for qtype, count in EXAM_CONFIG.items():
        query = db.query(Question).filter(Question.type == qtype)
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)

        pool = query.all()
        if not pool:
            continue

        # Prefer questions matching difficulty weights
        weighted = []
        for q in pool:
            weight = DIFFICULTY_WEIGHTS.get(q.difficulty, 10)
            weighted.extend([q] * weight)

        selected = _sample_unique(weighted, min(count, len(pool)), [q.id for q in exam_questions])
        exam_questions.extend(selected)

    random.shuffle(exam_questions)

    return {
        "exam_id": f"exam_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "total": len(exam_questions),
        "duration_minutes": len(exam_questions) * 2,  # ~2 min per question
        "questions": [
            {
                "id": q.id,
                "type": q.type,
                "stem": q.stem,
                "options": q.options,
                "subject_name": q.subject.name if q.subject else "",
            }
            for q in exam_questions
        ],
    }


@router.post("/submit")
def submit_exam(data: SubmitExam, db: Session = Depends(get_db)):
    """Submit all answers at once and get score report."""
    question_ids = list(data.answers.keys())
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    q_map = {str(q.id): q for q in questions}

    results = []
    correct_count = 0
    type_stats: dict[str, dict] = {
        "single_choice": {"correct": 0, "total": 0},
        "multi_choice": {"correct": 0, "total": 0},
        "calculation": {"correct": 0, "total": 0},
        "essay": {"correct": 0, "total": 0},
    }

    subject_stats: dict[str, dict] = {}

    for qid, user_answer in data.answers.items():
        q = q_map.get(qid)
        if not q:
            continue

        is_correct = q.answer.strip().upper() == user_answer.strip().upper()

        if is_correct:
            correct_count += 1

        # Type stats
        if q.type in type_stats:
            type_stats[q.type]["total"] += 1
            if is_correct:
                type_stats[q.type]["correct"] += 1

        # Subject stats
        sname = q.subject.name if q.subject else "未知"
        if sname not in subject_stats:
            subject_stats[sname] = {"correct": 0, "total": 0, "wrong_kps": {}}
        subject_stats[sname]["total"] += 1
        if is_correct:
            subject_stats[sname]["correct"] += 1
        else:
            for kp in q.knowledge_points:
                kp_name = kp.name
                subject_stats[sname]["wrong_kps"][kp_name] = \
                    subject_stats[sname]["wrong_kps"].get(kp_name, 0) + 1

        results.append({
            "question_id": int(qid),
            "your_answer": user_answer,
            "correct_answer": q.answer,
            "is_correct": is_correct,
            "stem": q.stem[:100],
            "explanation": q.explanation,
            "knowledge_points": [{"id": kp.id, "name": kp.name} for kp in q.knowledge_points],
            "type": q.type,
            "difficulty": q.difficulty,
        })

    total = len(questions)
    score = round(correct_count / total * 100, 1) if total > 0 else 0

    # Determine weak areas
    weak_kps = []
    for sname, stats in subject_stats.items():
        for kp_name, count in stats["wrong_kps"].items():
            weak_kps.append({"subject": sname, "knowledge_point": kp_name, "wrong_count": count})
    weak_kps.sort(key=lambda x: x["wrong_count"], reverse=True)

    return {
        "total": total,
        "correct": correct_count,
        "score": score,
        "type_breakdown": type_stats,
        "subject_breakdown": {
            name: {
                "correct": s["correct"],
                "total": s["total"],
                "accuracy": round(s["correct"] / s["total"] * 100, 1) if s["total"] > 0 else 0,
            }
            for name, s in subject_stats.items()
        },
        "weak_knowledge_points": weak_kps[:5],
        "results": results,
    }


def _sample_unique(pool: list, count: int, exclude_ids: list[int]) -> list:
    """Sample count items from pool, excluding those with IDs in exclude_ids."""
    available = [q for q in pool if q.id not in exclude_ids]
    if len(available) <= count:
        return available
    return random.sample(available, count)
