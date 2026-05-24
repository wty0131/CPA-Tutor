"""Example scraper for a CPA question bank website.

This is a template / demo scraper. Replace with real site-specific logic.
"""
from __future__ import annotations

import json
import logging

from scraper.base import BaseScraper, ScrapedQuestion

logger = logging.getLogger(__name__)


class DemoCPAScraper(BaseScraper):
    """Demonstration scraper that generates sample CPA questions for testing."""

    site_name = "demo_cpa_bank"
    base_url = "https://example.com/cpa"

    _SAMPLE_QUESTIONS = {
        "CPA-01": [
            {
                "type": "single_choice",
                "stem": "甲公司2023年1月1日购入乙公司30%的股权，支付价款5000万元。乙公司2023年度实现净利润2000万元，宣告分配现金股利500万元。甲公司对乙公司投资采用权益法核算。则甲公司2023年末长期股权投资的账面价值为（ ）万元。",
                "options": [
                    {"label": "A", "text": "5,000"}, {"label": "B", "text": "5,450"},
                    {"label": "C", "text": "5,600"}, {"label": "D", "text": "5,150"},
                ],
                "answer": "B",
                "explanation": "权益法下，长期股权投资初始成本5000万 + 按持股比例享有净利润2000×30%=600万 - 分得现金股利500×30%=150万 = 5450万",
                "difficulty": 2,
            },
            {
                "type": "single_choice",
                "stem": "下列各项中，不应计入存货成本的是（ ）。",
                "options": [
                    {"label": "A", "text": "购买价款"}, {"label": "B", "text": "进口关税"},
                    {"label": "C", "text": "运输途中的合理损耗"}, {"label": "D", "text": "一般纳税人增值税进项税额"},
                ],
                "answer": "D",
                "explanation": "一般纳税人增值税进项税额可以抵扣，不计入存货成本。其他三项均构成存货的采购成本。",
                "difficulty": 1,
            },
        ],
        "CPA-04": [
            {
                "type": "single_choice",
                "stem": "某企业2023年度应纳税所得额为800万元，适用的企业所得税税率为25%。该企业当年发生新产品研发费用200万元（符合加计扣除条件），则当年应缴纳的企业所得税为（ ）万元。",
                "options": [
                    {"label": "A", "text": "200"}, {"label": "B", "text": "150"},
                    {"label": "C", "text": "162.5"}, {"label": "D", "text": "175"},
                ],
                "answer": "C",
                "explanation": "应纳所得税 = (800-200×100%)×25% = 600×25% = 150万。注意研发费用加计扣除100%，应纳税所得额调减200万。",
                "difficulty": 2,
            },
        ],
        "CPA-05": [
            {
                "type": "single_choice",
                "stem": "根据《公司法》的规定，有限责任公司股东会作出修改公司章程的决议，必须经代表（ ）以上表决权的股东通过。",
                "options": [
                    {"label": "A", "text": "1/2"}, {"label": "B", "text": "2/3"},
                    {"label": "C", "text": "3/4"}, {"label": "D", "text": "全部"},
                ],
                "answer": "B",
                "explanation": "《公司法》规定，修改公司章程、增加或减少注册资本的决议，以及公司合并、分立、解散或变更公司形式的决议，须经代表三分之二以上表决权的股东通过。",
                "difficulty": 1,
            },
        ],
    }

    def scrape(self, subject_code: str | None = None) -> list[ScrapedQuestion]:
        codes = [subject_code] if subject_code else list(self._SAMPLE_QUESTIONS.keys())
        results: list[ScrapedQuestion] = []
        for code in codes:
            for q in self._SAMPLE_QUESTIONS.get(code, []):
                results.append(ScrapedQuestion(
                    subject_code=code,
                    type=q["type"],
                    stem=q["stem"],
                    options=q["options"],
                    answer=q["answer"],
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", 1),
                    source_url=self.base_url,
                ))
        logger.info("Demo scraper: generated %d questions", len(results))
        return results
