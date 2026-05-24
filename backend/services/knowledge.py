"""Knowledge point management and AI-powered summarization."""
from __future__ import annotations

import logging

from core.ai_client import get_ai_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深的CPA（注册会计师）考试辅导专家。你的任务是对特定知识点进行归纳总结。

请严格按照JSON格式返回：
{
  "summary": "知识点归纳总结（300-500字）",
  "key_concepts": ["核心概念1", "核心概念2"],
  "common_mistakes": ["常见错误1", "常见错误2"],
  "exam_frequency": "高频/中频/低频",
  "tips": ["备考建议1", "备考建议2"]
}"""


def summarize_knowledge_point(kp_name: str, subject_name: str, questions: list[dict]) -> dict:
    """Generate AI summary for a knowledge point based on associated questions."""
    client = get_ai_client()

    question_texts = "\n".join(
        f"- {q.get('stem', '')[:200]}" for q in questions[:10]
    )

    prompt = f"""请对以下CPA知识点进行归纳总结：

科目：{subject_name}
知识点：{kp_name}
关联题目数量：{len(questions)}
部分题目示例（用于分析考点频率和出题规律）：
{question_texts if question_texts else "暂无相关题目"}

请分析该知识点的核心内容、考试常见出题方式、以及备考要点。"""

    result = client.send_json(prompt, SYSTEM_PROMPT, temperature=0.3)
    if not result or "raw" in result:
        return {
            "summary": f"{kp_name}的详细总结待生成。",
            "key_concepts": [],
            "common_mistakes": [],
            "exam_frequency": "未知",
            "tips": [],
        }
    return result


def analyze_weak_points(wrong_answers: list[dict]) -> dict:
    """Analyze user's weak knowledge points based on wrong answer history."""
    client = get_ai_client()

    kp_counts: dict[str, int] = {}
    for wa in wrong_answers:
        for kp in wa.get("knowledge_points", []):
            kp_name = kp.get("name", "") if isinstance(kp, dict) else kp
            kp_counts[kp_name] = kp_counts.get(kp_name, 0) + 1

    sorted_kps = sorted(kp_counts.items(), key=lambda x: x[1], reverse=True)
    kp_list = "\n".join(f"- {name}: 错题数 {count}" for name, count in sorted_kps[:10])

    prompt = f"""用户错题知识点分布：
{kp_list if kp_list else "暂无错题数据"}

请给出薄弱知识点分析建议，返回JSON格式：
{{
  "weak_points": ["最薄弱的知识点1"],
  "analysis": "整体薄弱分析（200字）",
  "study_plan": "针对性复习计划建议"
}}"""

    result = client.send_json(prompt, SYSTEM_PROMPT, temperature=0.3)
    return result if result and "raw" not in result else {}
