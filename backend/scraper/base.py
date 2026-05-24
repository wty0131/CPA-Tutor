"""Abstract base class for question scrapers."""
from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup

from core.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ScrapedQuestion:
    subject_code: str
    type: str  # single_choice / multi_choice / calculation / essay
    stem: str
    options: list[dict[str, str]]
    answer: str
    explanation: str = ""
    difficulty: int = 1
    source_url: str = ""


class BaseScraper(ABC):
    site_name: str = "unknown"
    base_url: str = ""

    def __init__(self) -> None:
        cfg = get_config()
        self._client = httpx.Client(
            headers={"User-Agent": cfg.scraping_user_agent},
            timeout=30,
            follow_redirects=True,
        )
        self._delay = cfg.scraping_request_delay

    @abstractmethod
    def scrape(self, subject_code: str | None = None) -> list[ScrapedQuestion]:
        """Fetch and parse questions. Return list of ScrapedQuestion."""

    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch a URL and return a BeautifulSoup object."""
        import time

        time.sleep(self._delay)
        resp = self._client.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")

    @staticmethod
    def hash_question(stem: str) -> str:
        return hashlib.md5(stem.strip().encode()).hexdigest()

    def close(self) -> None:
        self._client.close()
