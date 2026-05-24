"""AI explanation generation service."""
from __future__ import annotations

import json
import logging

from core.ai_client import get_ai_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深的CPA（注册会计师）考试辅导专家。你的任务是为CPA考题生成详细的解析和知识点标注。

请严格按照JSON格式返回，不要包含其他内容：
{
  "explanation": "详细解析，包含解题思路、计算过程（如有）、涉及的知识点说明",
  "knowledge_points": ["知识点1", "知识点2"],
  "difficulty": 1-5
}

解析要求：
1. 逐步骤分析解题思路，逻辑清晰
2. 对计算题给出完整计算过程和公式
3. 标注每个涉及的知识点名称
4. 难度评级：1=基础概念 2=简单应用 3=综合分析 4=复杂计算 5=综合难题"""


def generate_explanation(question: dict) -> dict:
    """Generate AI explanation for a question. Returns dict with explanation, knowledge_points, difficulty."""
    client = get_ai_client()

    prompt = f"""请为以下CPA考题生成解析：

科目：{question.get('subject_name', '')}
题型：{question.get('type', 'single_choice')}
题目：{question.get('stem', '')}
选项：{json.dumps(question.get('options', []), ensure_ascii=False)}
正确答案：{question.get('answer', '')}"""

    result = client.send_json(prompt, SYSTEM_PROMPT, temperature=0.3)
    if not result or "raw" in result:
        logger.warning("AI explanation generation failed or returned non-JSON")
        return {
            "explanation": question.get("explanation", ""),
            "knowledge_points": [],
            "difficulty": 1,
        }
    return result


def annotate_question_with_ai(question: dict) -> dict:
    """Annotate a raw question with AI-generated explanation and knowledge points."""
    result = generate_explanation(question)
    question["explanation"] = result.get("explanation", "")
    question["knowledge_points"] = result.get("knowledge_points", [])
    question["difficulty"] = result.get("difficulty", 1)
    return question
