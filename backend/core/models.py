"""SQLAlchemy ORM models for CPA Tutor."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Table,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    pass


# Association table: questions <-> knowledge_points
question_kp_map = Table(
    "question_kp_map",
    Base.metadata,
    Column("question_id", ForeignKey("questions.id"), primary_key=True),
    Column("kp_id", ForeignKey("knowledge_points.id"), primary_key=True),
)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")

    knowledge_points: Mapped[list["KnowledgePoint"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_points.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")

    subject: Mapped[Subject] = relationship(back_populates="knowledge_points")
    parent: Mapped["KnowledgePoint | None"] = relationship(
        "KnowledgePoint", back_populates="children", remote_side="KnowledgePoint.id"
    )
    children: Mapped[list["KnowledgePoint"]] = relationship(
        "KnowledgePoint", back_populates="parent", cascade="all, delete-orphan",
    )
    questions: Mapped[list["Question"]] = relationship(
        secondary=question_kp_map, back_populates="knowledge_points"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="single_choice")
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    answer: Mapped[str] = mapped_column(String(200), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    source_url: Mapped[str] = mapped_column(String(500), default="")
    source_site: Mapped[str] = mapped_column(String(100), default="")
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    subject: Mapped[Subject] = relationship(back_populates="questions")
    knowledge_points: Mapped[list[KnowledgePoint]] = relationship(
        secondary=question_kp_map, back_populates="questions"
    )
    wrong_answers: Mapped[list["WrongAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class WrongAnswer(Base):
    __tablename__ = "wrong_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    user_answer: Mapped[str] = mapped_column(String(200), default="")
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    mastery_level: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes: Mapped[str] = mapped_column(Text, default="")
    # SM-2 fields
    ease_factor: Mapped[float] = mapped_column(default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[Question] = relationship(back_populates="wrong_answers")
