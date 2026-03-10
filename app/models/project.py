from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models import Task


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    deadline: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    owner_uid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    color_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_reviews = relationship(
        "AIReview", back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[list[Task]] = relationship("Task", back_populates="project")
