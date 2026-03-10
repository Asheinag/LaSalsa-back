from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models import Project


# This is a SQLAlchemy model for the Task table
class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    planned_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    project: Mapped[Project | None] = relationship("Project", back_populates="tasks")
    owner_uid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )
    pomodoro_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pomodoros.id"), nullable=True
    )
    ai_reviews = relationship(
        "AIReview", back_populates="task", cascade="all, delete-orphan"
    )
