"""Background scheduler for periodic scraping tasks."""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_scrape_task: asyncio.Task | None = None


async def run_periodic_scrape(interval_hours: int = 24):
    """Periodically scrape questions from all sources."""
    while True:
        try:
            from scraper.registry import run_scrape
            from core.database import get_session
            from core.models import Question, Subject, KnowledgePoint
            from services.explanation import annotate_question_with_ai

            questions = run_scrape()
            if questions:
                db = get_session()
                try:
                    saved = 0
                    for q in questions:
                        subj = db.query(Subject).filter(Subject.code == q.subject_code).first()
                        if not subj:
                            continue

                        # Check duplicate by stem hash
                        from scraper.base import BaseScraper
                        stem_hash = BaseScraper.hash_question(q.stem)
                        # Store in memory set for this run
                        existing = db.query(Question).filter(
                            Question.stem.like(f"{q.stem[:50]}%")
                        ).first()
                        if existing:
                            continue

                        question_dict = {
                            "subject_name": subj.name,
                            "type": q.type,
                            "stem": q.stem,
                            "options": q.options,
                            "answer": q.answer,
                        }
                        annotated = annotate_question_with_ai(question_dict)

                        question = Question(
                            subject_id=subj.id,
                            type=q.type,
                            stem=q.stem,
                            options=q.options,
                            answer=q.answer,
                            explanation=annotated.get("explanation", q.explanation),
                            difficulty=annotated.get("difficulty", q.difficulty),
                            source_url=q.source_url,
                            source_site="scraper",
                        )
                        db.add(question)
                        db.flush()

                        # Map knowledge points
                        for kp_name in annotated.get("knowledge_points", []):
                            kp = db.query(KnowledgePoint).filter(
                                KnowledgePoint.subject_id == subj.id,
                                KnowledgePoint.name == kp_name,
                            ).first()
                            if kp:
                                question.knowledge_points.append(kp)

                        saved += 1
                    db.commit()
                    logger.info("Periodic scrape saved %d new questions", saved)
                except Exception as e:
                    logger.error("Periodic scrape save failed: %s", e)
                    db.rollback()
                finally:
                    db.close()
        except Exception as e:
            logger.error("Periodic scrape error: %s", e)

        await asyncio.sleep(interval_hours * 3600)
