from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# Модель Помодоро для отслеживания сеансов работы
class Pomodoro(Base):
    __tablename__ = "pomodoros"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_uid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=25)
    previous_pomodoro_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
