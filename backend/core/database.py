"""Database engine and session management."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_config
from core.models import Base

_engine = None
_SessionLocal: sessionmaker | None = None


def get_engine():
    global _engine
    if _engine is None:
        cfg = get_config()
        db_url = cfg.db_url
        if db_url.startswith("sqlite:///./"):
            rel = db_url.removeprefix("sqlite:///./")
            abs_path = Path(__file__).parent.parent / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{abs_path}"

        _engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
            echo=False,
        )
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def init_db():
    """Create all tables and seed initial data."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    _seed_subjects()


def _seed_subjects():
    """Seed the 6 CPA subjects and basic knowledge point tree from config."""
    cfg = get_config()
    subjects_data = cfg.subjects

    with get_session() as db:
        from core.models import Subject, KnowledgePoint

        existing = db.query(Subject).count()
        if existing >= 6:
            return

        for s in subjects_data:
            subj = Subject(code=s["code"], name=s["name"], description=s.get("description", ""))
            db.add(subj)
            db.flush()
            # Add some basic knowledge point chapters per subject
            chapters = _default_chapters(s["code"])
            for ch_name in chapters:
                kp = KnowledgePoint(
                    subject_id=subj.id,
                    parent_id=None,
                    name=ch_name,
                    level=0,
                )
                db.add(kp)
        db.commit()


def _default_chapters(code: str) -> list[str]:
    """Return default chapter names for each CPA subject."""
    chapters_map = {
        "CPA-01": [
            "总论", "存货", "固定资产", "无形资产", "投资性房地产",
            "长期股权投资", "资产减值", "负债", "职工薪酬", "股份支付",
            "所有者权益", "收入", "费用和利润", "财务报告", "合并财务报表",
        ],
        "CPA-02": [
            "审计概述", "审计计划", "审计证据", "审计抽样", "风险评估",
            "风险应对", "审计报告", "内部控制审计", "职业道德", "审计业务",
        ],
        "CPA-03": [
            "财务管理基础", "财务报表分析", "资本成本", "资本预算",
            "营运资本管理", "成本计算", "本量利分析", "预算管理",
        ],
        "CPA-04": [
            "增值税", "消费税", "企业所得税", "个人所得税",
            "土地增值税", "印花税", "税收征管法", "国际税收",
        ],
        "CPA-05": [
            "公司法", "合伙企业法", "合同法", "证券法",
            "破产法", "票据法", "反垄断法", "支付结算法律制度",
        ],
        "CPA-06": [
            "战略与战略管理", "战略分析", "战略选择", "战略实施",
            "公司治理", "风险管理", "内部控制", "企业绩效评价",
        ],
    }
    return chapters_map.get(code, ["第一章", "第二章", "第三章"])
