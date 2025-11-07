from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# Это модель SQLAlchemy для таблицы TaskAIComments
class TaskAIComment(Base):
    __tablename__ = "task_ai_comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )
    task = relationship("Task", back_populates="ai_comments")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    owner_uid: Mapped[str] = mapped_column(String, nullable=False, index=True, server_default='owner_user_uid')
