"""Annotate existing questions with knowledge points via AI."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from core.database import init_db, get_session
from core.models import Subject, KnowledgePoint, Question
from core.ai_client import get_ai_client

SYSTEM_PROMPT = """你是一位资深CPA考试辅导专家。请根据题目内容判断它属于哪个或哪些知识点。

返回JSON格式：
{
  "knowledge_points": ["知识点名称1", "知识点名称2"],
  "difficulty": 1-5
}

注意：
1. 知识点名称应该与CPA官方教材的章节/考点名称一致
2. 一道题可能涉及多个知识点（跨章节综合题）
3. 直接返回JSON，不要其他文字"""


def get_existing_kps(db, subject_id: int) -> dict[str, KnowledgePoint]:
    """Get existing knowledge points as {name: obj} dict."""
    kps = db.query(KnowledgePoint).filter(
        KnowledgePoint.subject_id == subject_id
    ).all()
    return {kp.name: kp for kp in kps}


def create_kp(db, subject_id: int, name: str, parent_id: int | None = None, level: int = 2) -> KnowledgePoint:
    """Create a new knowledge point under the given subject."""
    kp = KnowledgePoint(
        subject_id=subject_id,
        parent_id=parent_id,
        name=name,
        level=level,
    )
    db.add(kp)
    db.flush()
    return kp


def find_or_create_kp(db, subject_id: int, name: str, kp_cache: dict) -> KnowledgePoint:
    """Find existing KP or create new one."""
    if name in kp_cache:
        return kp_cache[name]

    # Find matching chapter (level=0) to set as parent
    chapters = db.query(KnowledgePoint).filter(
        KnowledgePoint.subject_id == subject_id,
        KnowledgePoint.level == 0,
    ).all()

    # Try to find best parent chapter by keyword matching
    parent = None
    for ch in chapters:
        if any(kw in name for kw in ch.name.split("、")) or any(c in name for c in ch.name):
            parent = ch
            break

    kp = create_kp(db, subject_id, name, parent_id=parent.id if parent else None, level=2)
    kp_cache[name] = kp
    return kp


def annotate_question(db, question: Question, kp_cache: dict) -> int:
    """Annotate a single question with knowledge points. Returns number of KPs linked."""
    client = get_ai_client()

    prompt = f"""请判断以下CPA考题涉及的知识点：

科目：{question.subject.name}
题型：{question.type}
题目：{question.stem}
选项：{json.dumps(question.options, ensure_ascii=False) if question.options else '无'}
答案：{question.answer}"""

    result = client.send_json(prompt, SYSTEM_PROMPT, temperature=0.1)

    kp_names = result.get("knowledge_points", [])
    if isinstance(kp_names, str):
        kp_names = [kp_names]

    linked = 0
    for kp_name in kp_names:
        if not kp_name or len(kp_name) > 100:
            continue
        kp = find_or_create_kp(db, question.subject_id, kp_name, kp_cache)
        if kp not in question.knowledge_points:
            question.knowledge_points.append(kp)
            linked += 1

    if result.get("difficulty"):
        try:
            question.difficulty = int(result["difficulty"])
        except:
            pass

    return linked


def main():
    init_db()
    client = get_ai_client()
    if not client.is_available:
        print("ERROR: AI not available")
        return

    db = get_session()

    # Get questions without knowledge points
    questions = db.query(Question).all()
    total = len(questions)
    print(f"Found {total} questions to annotate")
    print("=" * 50)

    # Pre-load all KPs per subject
    kp_caches: dict[int, dict] = {}
    for subj in db.query(Subject).all():
        kp_caches[subj.id] = get_existing_kps(db, subj.id)
        print(f"  {subj.name}: {len(kp_caches[subj.id])} existing KPs")

    print()
    annotated = 0
    total_links = 0

    for i, q in enumerate(questions):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{total}...")

        try:
            cache = kp_caches.get(q.subject_id, {})
            linked = annotate_question(db, q, cache)
            total_links += linked
            if linked > 0:
                annotated += 1
        except Exception as e:
            print(f"  Error on Q{q.id}: {e}")
            continue

    db.commit()

    # Summary
    print(f"\n{'='*50}")
    print(f"  Questions annotated: {annotated}/{total}")
    print(f"  Total KP links:      {total_links}")
    print(f"{'='*50}")

    # Show new KP counts per subject
    print("\nKnowledge Points per subject:")
    for subj in db.query(Subject).all():
        total_kps = db.query(KnowledgePoint).filter(
            KnowledgePoint.subject_id == subj.id
        ).count()
        linked_kps = db.query(KnowledgePoint).filter(
            KnowledgePoint.subject_id == subj.id,
            KnowledgePoint.questions.any(),
        ).count()
        print(f"  {subj.name}: {linked_kps}/{total_kps} with questions")

    db.close()


if __name__ == "__main__":
    main()
