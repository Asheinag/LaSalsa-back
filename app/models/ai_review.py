from datetime import datetime

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# Это модель SQLAlchemy для таблицы AIReview
class AIReview(Base):
    __tablename__ = "ai_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    task = relationship("Task", back_populates="ai_reviews")
    project = relationship("Project", back_populates="ai_reviews")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    owner_uid: Mapped[str] = mapped_column(
        String, nullable=False, index=True, server_default="owner_user_uid"
    )
    __table_args__ = (
        CheckConstraint(
            "(task_id IS NOT NULL AND project_id IS NULL) OR "
            "(task_id IS NULL AND project_id IS NOT NULL)",
            name="ck_ai_review_single_owner",
        ),
    )
