import json
from collections.abc import Sequence
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.common import TaskStatus
from app.database import get_sync_session
from app.models import AIReview, Project, Task
from app.services import LLM

llm = LLM()

logger = get_task_logger(__name__)


def validate_owner(user_uid: str, review: AIReview) -> bool:
    """Check if the review belongs to the user."""
    return review.owner_uid == user_uid


@celery_app.task(name="app.tasks.make_ai_task_review")
def run_task_review(user_uid: str, task_id: int) -> dict[str, Any]:
    """
    Фоновая задача для обзора задач с помощью ИИ.
    """
    with get_sync_session() as session:
        task_name, project_name = _get_task_and_project_name(session, task_id, user_uid)
        comment = llm.get_task_review(task_name, project_name)
        _deactivate_active_reviews(session, user_uid, task_id=task_id)
        _write_new_active_review(session, user_uid, comment, task_id=task_id)
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


def _deactivate_active_reviews(
    session: Session,
    user_uid: str,
    task_id: int | None = None,
    project_id: int | None = None,
) -> None:
    """
    Деактивация всех предыдущих комментариев
    """
    session.execute(
        update(AIReview)
        .where(
            AIReview.task_id == task_id,
            AIReview.project_id == project_id,
            AIReview.is_active,
            AIReview.owner_uid == user_uid,
        )
        .values(is_active=False)
    ).scalars().all()


def _write_new_active_review(
    session: Session, user_uid: str, comment: str, task_id: int | None = None, project_id: int | None = None,
) -> None:
    """
    Сохранение нового активного комментария
    """
    review = AIReview(
        task_id=task_id,
        project_id=project_id,
        owner_uid=user_uid,
        comment=json.dumps(comment, ensure_ascii=False),
        is_active=True,
    )

    session.add(review)


async def get_last_active_review(
    db: AsyncSession, user_uid: str, task_id: int | None = None, project_id: int | None = None,
) -> AIReview:
    """
    Получение последнего активного ревью задачи
    """
    result = await db.execute(
        select(AIReview).where(
            AIReview.task_id == task_id,
            AIReview.project_id == project_id,
            AIReview.is_active,
            AIReview.owner_uid == user_uid,
        )
    )
    return result.scalars().one()


async def get_all_comments(
    db: AsyncSession, user_uid: str, task_id: int | None = None, project_id: int | None = None
) -> Sequence[AIReview]:
    """
    Получение всех комментариев по задаче и активных и нет
    """
    history = await db.execute(
        select(AIReview).where(
            AIReview.task_id == task_id, AIReview.project_id == project_id, AIReview.owner_uid == user_uid
        )
    )
    return history.scalars().all()


async def get_review_by_id(db: AsyncSession, review_id: int, user_uid: str) -> AIReview:
    """
    Получение ревью по его ID
    """
    review = await db.get(AIReview, review_id)
    if not review:
        return None
    if not validate_owner(user_uid, review):
        return None

    return review


@celery_app.task(name="app.tasks.make_ai_project_review")
def run_project_review(user_uid: str, project_id: int) -> dict[str, Any]:
    """
    Запускаем процесс получения ревью по проекту и его задачам
    """
    with get_sync_session() as session:
        project = _get_project_by_id(session, project_id, user_uid)
        task_info = _get_project_tasks_info(session, project_id, user_uid)
        comment = llm.get_project_review(
            project_name=project.name,
            completed_tasks=task_info.get("completed"),
            total_tasks=task_info.get("total"),
            active_tasks=task_info.get("active_names"),
        )
        _deactivate_active_reviews(session, user_uid, project_id=project_id)
        _write_new_active_review(session, user_uid, comment, project_id=project_id)
        session.commit()

    return {"status": "done", "project_id": project_id, "review": comment}


def _get_project_by_id(session: Session, project_id: int, user_uid: str) -> Project:
    """
    Получаем проект по ID
    """
    return session.execute(
        select(Project).where(Project.id == project_id, Project.owner_uid == user_uid)
    ).scalars().one()


def _get_project_tasks_info(
    session: Session, project_id: int, user_uid: int
) -> dict[str, Any]:
    """
    Получаем информацию об активных и выполненных задачах проекта
    """
    result = session.execute(
        select(
            func.count().label("total"),
            func.sum(case((Task.status == TaskStatus.DONE.value, 1), else_=0)).label(
                "completed"
            ),
        ).where(Task.project_id == project_id)
    ).one()

    total_tasks = result.total
    completed_tasks = result.completed

    active_task_names = (
        session.execute(
            select(Task.name)
            .where(Task.project_id == project_id, Task.status != TaskStatus.DONE.value)
            .limit(30)
        )
        .scalars()
        .all()
    )

    return {
        "total": total_tasks,
        "completed": completed_tasks,
        "active_names": active_task_names,
    }
