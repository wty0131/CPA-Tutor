"""Scraper registry — maps CPA subjects to scraper implementations."""
from __future__ import annotations

import logging
from typing import Any

from scraper.base import BaseScraper, ScrapedQuestion

logger = logging.getLogger(__name__)

_registry: dict[str, list[BaseScraper]] = {}


def register_scraper(subject_code: str, scraper: BaseScraper) -> None:
    """Register a scraper for a CPA subject code."""
    _registry.setdefault(subject_code, []).append(scraper)
    logger.info("Registered scraper %s for %s", scraper.site_name, subject_code)


def get_scrapers(subject_code: str | None = None) -> list[BaseScraper]:
    """Get all scrapers, optionally filtered by subject."""
    if subject_code:
        return _registry.get(subject_code, [])
    result: list[BaseScraper] = []
    for scrapers in _registry.values():
        result.extend(scrapers)
    return result


def run_scrape(subject_code: str | None = None) -> list[ScrapedQuestion]:
    """Run all registered scrapers and collect results."""
    all_questions: list[ScrapedQuestion] = []
    scrapers = get_scrapers(subject_code)
    for scraper in scrapers:
        try:
            questions = scraper.scrape(subject_code)
            all_questions.extend(questions)
            logger.info(
                "Scraper %s fetched %d questions for %s",
                scraper.site_name, len(questions), subject_code or "all",
            )
        except Exception as e:
            logger.error("Scraper %s failed: %s", scraper.site_name, e)
        finally:
            scraper.close()
    return all_questions
