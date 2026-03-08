from collections.abc import Sequence
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import get_sync_session
from app.models import AIReview, Task
from app.services import LLM

llm = LLM()

logger = get_task_logger(__name__)


def validate_owner(user_uid: str, review: AIReview) -> bool:
    """Check if the review belongs to the user."""
    return review.owner_uid == user_uid


@celery_app.task(name="app.tasks.make_ai_review")
def run_task_review(user_uid: str, task_id: int) -> dict[str, Any]:
    """
    Фоновая задача для обзора задач с помощью ИИ.
    """
    with get_sync_session() as session:
        # Получить имена проекта и задачи для формирования запроса к LLM
        task_name, project_name = _get_task_and_project_name(session, task_id, user_uid)
        # Отправить запрос в llm
        comment = llm.get_task_review(task_name, project_name)
        # деактивировать активные ревью
        _deactivate_active_reviews_by_task_id(session, task_id, user_uid)
        # Записать новый комментарий АИшки к задаче
        _write_new_active_review_for_task(session, task_id, user_uid, comment)
        # Коммит одной транзакцией
        session.commit()

    return {"status": "done", "task_id": task_id, "review": comment}


def _get_task_and_project_name(
    session: Session, task_id: int, user_uid: str
) -> tuple[str, str | None]:
    """
    Получение Наименования задачи и проекта, если есть.
    """
    task = (
        session.execute(
            select(Task).where(Task.id == task_id, Task.owner_uid == user_uid)
        )
        .scalars()
        .one()
    )

    task_name = task.name
    project_name = task.project.name if task.project else None

    return task_name, project_name


def _deactivate_active_reviews_by_task_id(
    session: Session, task_id: int, user_uid: str
) -> None:
    """
    Деактивация всех предыдущих комментариев
    """
    session.execute(
        update(AIReview)
        .where(
            AIReview.task_id == task_id,
            AIReview.is_active,
            AIReview.owner_uid == user_uid,
        )
        .values(is_active=False)
    ).scalars().all()


def _write_new_active_review_for_task(
    session: Session, task_id: int, user_uid: str, comment: str
) -> None:
    """
    Сохранение нового активного комментария
    """
    review = AIReview(
        task_id=task_id,
        owner_uid=user_uid,
        comment=comment,
        is_active=True,
    )

    session.add(review)


async def get_last_active_review_by_task_id(
    db: AsyncSession, task_id: str, user_uid: str
) -> AIReview:
    """
    Получение последнего активного ревью
    """
    result = await db.execute(
        select(AIReview).where(
            AIReview.task_id == task_id,
            AIReview.is_active,
            AIReview.owner_uid == user_uid,
        )
    )
    return result.scalars().one()


async def get_all_comments_by_task_id(
    db: AsyncSession, task_id: int, user_uid: str
) -> Sequence[AIReview]:
    """
    Получение всех комментариев по задаче и активных и нет
    """
    history = await db.execute(
        select(AIReview).where(
            AIReview.task_id == task_id, AIReview.owner_uid == user_uid
        )
    )
    return history.scalars().all()


async def get_review_by_id(db: AsyncSession, review_id: int, user_uid: str) -> AIReview:
    review = await db.get(review_id)
    if not review:
        return None
    if not validate_owner(user_uid, review):
        return None

    return review
