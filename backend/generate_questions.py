"""Batch generate CPA questions using DeepSeek API."""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.database import init_db, get_session
from core.models import Subject, Question
from core.ai_client import get_ai_client

SYSTEM_PROMPT = """你是一位资深的中国注册会计师(CPA)考试命题专家。请严格按照要求生成高质量的CPA考试题目。

返回JSON数组格式，每道题格式如下：
{
  "questions": [
    {
      "type": "single_choice",
      "stem": "题目题干，内容要专业、准确，符合CPA考试风格和难度",
      "options": [
        {"label": "A", "text": "选项内容"},
        {"label": "B", "text": "选项内容"},
        {"label": "C", "text": "选项内容"},
        {"label": "D", "text": "选项内容"}
      ],
      "answer": "B",
      "explanation": "详细解析，包含计算过程、法律依据或会计准则依据",
      "difficulty": 2
    }
  ]
}

要求：
1. 题目必须符合中国CPA考试的真实出题风格和难度
2. 计算题要有完整的数据和计算过程
3. 法律题要引用具体法条
4. 难度1-5：1=基础概念，2=简单应用，3=综合分析，4=复杂计算，5=综合难题
5. 每个科目的题目要覆盖多个章节/知识点
6. 选项要有强干扰性（错误选项看起来也合理）
7. 直接返回JSON，不要任何其他文字"""

SUBJECT_CONFIGS = {
    "CPA-01": {
        "name": "会计",
        "topics": "长期股权投资、合并财务报表、收入确认、金融工具、租赁、资产减值、所得税会计",
        "count": 20,
    },
    "CPA-02": {
        "name": "审计",
        "topics": "审计证据、风险评估、内部控制、审计报告、职业道德、审计抽样、实质性程序",
        "count": 20,
    },
    "CPA-03": {
        "name": "财务成本管理",
        "topics": "资本成本计算、资本预算、财务报表分析、本量利分析、营运资本管理、企业价值评估",
        "count": 20,
    },
    "CPA-04": {
        "name": "税法",
        "topics": "增值税计算、企业所得税汇算清缴、个人所得税综合所得、消费税、土地增值税、税收优惠政策",
        "count": 20,
    },
    "CPA-05": {
        "name": "经济法",
        "topics": "公司法制度、合同法律制度、证券法、破产法、票据法、合伙企业法",
        "count": 20,
    },
    "CPA-06": {
        "name": "公司战略与风险管理",
        "topics": "SWOT分析、五力模型、战略选择、公司治理、风险管理框架、内部控制、平衡计分卡",
        "count": 20,
    },
}


def generate_for_subject(code: str, cfg: dict) -> list[dict]:
    client = get_ai_client()
    questions = []

    # Generate in batches to avoid token limits
    batch_size = 5
    total = cfg["count"]
    topic_list = cfg["topics"].split("、")

    for batch_start in range(0, total, batch_size):
        batch_topics = topic_list[batch_start % len(topic_list):]
        topics_str = "、".join(batch_topics[:3])

        prompt = f"""请生成{batch_size}道{cfg["name"]}({code})科目的CPA考试题目。

主要覆盖知识点：{topics_str}

题型分配：3道单选题(single_choice)、1道多选题(multi_choice)、1道计算题(calculation)

直接返回JSON数组。"""

        print(f"  Generating batch {batch_start // batch_size + 1}...")
        result = client.send_json(prompt, SYSTEM_PROMPT, temperature=0.5)

        # Handle both {"questions": [...]} and direct [...] responses
        if isinstance(result, list):
            batch_questions = result
        elif "raw" in result:
            # AI returned non-JSON, skip
            print(f"    AI returned non-JSON response, skipping")
            continue
        else:
            batch_questions = result.get("questions", [])
        questions.extend(batch_questions)
        print(f"    Got {len(batch_questions)} questions")

    return questions


def save_questions(code: str, questions: list[dict]) -> int:
    db = get_session()
    subj = db.query(Subject).filter(Subject.code == code).first()
    if not subj:
        print(f"  Subject {code} not found!")
        db.close()
        return 0

    saved = 0
    for q in questions:
        # Skip if missing required fields
        if not q.get("stem") or not q.get("answer"):
            continue

        # Check for duplicate
        existing = db.query(Question).filter(
            Question.stem == q["stem"],
            Question.subject_id == subj.id,
        ).first()
        if existing:
            continue

        options = q.get("options", [])
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except:
                options = []

        question = Question(
            subject_id=subj.id,
            type=q.get("type", "single_choice"),
            stem=q["stem"],
            options=options,  # pass list directly, SQLAlchemy JSON handles serialization
            answer=q.get("answer", ""),
            explanation=q.get("explanation", ""),
            difficulty=q.get("difficulty", 1),
            source_site="ai-generated",
        )
        db.add(question)
        saved += 1

    db.commit()
    db.close()
    return saved


def main():
    init_db()
    client = get_ai_client()
    if not client.is_available:
        print("ERROR: AI API key not configured!")
        return

    print("=" * 50)
    print("  CPA Question Generator")
    print("=" * 50)

    total_generated = 0
    total_saved = 0

    for code, cfg in SUBJECT_CONFIGS.items():
        print(f"\n{'='*40}")
        print(f"  {code} {cfg['name']}: generating {cfg['count']} questions")
        print(f"{'='*40}")

        try:
            questions = generate_for_subject(code, cfg)
            total_generated += len(questions)

            # Fix up questions before saving
            for q in questions:
                # Multi-choice answers come as list, convert to comma string
                if isinstance(q.get("answer"), list):
                    q["answer"] = ",".join(q["answer"])
                # Ensure options are proper dicts
                opts = q.get("options", [])
                if isinstance(opts, str):
                    try:
                        q["options"] = json.loads(opts)
                    except:
                        q["options"] = []
                # Ensure difficulty is int
                q["difficulty"] = int(q.get("difficulty", 1))
                # Ensure type is valid
                if q.get("type") not in ("single_choice", "multi_choice", "calculation", "essay"):
                    q["type"] = "single_choice"

            saved = save_questions(code, questions)
            total_saved += saved
            print(f"  -> Saved {saved} new questions for {cfg['name']}")
        except Exception as e:
            import traceback
            print(f"  ERROR: {e}")
            traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"  Total generated: {total_generated}")
    print(f"  Total saved:     {total_saved}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
