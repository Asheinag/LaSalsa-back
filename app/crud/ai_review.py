from collections.abc import Sequence
from datetime import datetime
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.common import TaskStatus
from app.database import get_sync_session
from app.models import AIReview, Task
from app.services import get_task_review

logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.make_ai_review")
def run_task_review(user_uid: str, task_id: int) -> dict[str, Any]:
    """
    Фоновая задача для обзора задач с помощью ИИ.
    """

    with get_sync_session() as session:
        # Получаем задачу по id
        task = session.execute(
            select(Task)
            .where(
                Task.id == task_id,
                Task.owner_uid == user_uid
            )
        ).scalars().one()


        task_name = task.name
        project_name = task.project.name if task.project else None

        # Отправить запрос в llm
        result = get_task_review(task_name, project_name)

    return {"status": "done", "task id": task_id, "query": result}




def _collect_tasks_for_ai_review_by_project(
    session: Session,
    user_uid: str,
    project_id: int,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[Task]:
    """
    Собираем задачи пользователя для обзора ИИ.
    """
    logger.info(
        "Collecting tasks for AI review for project_id=%d user_uid=%s, offset=%d, limit=%d",
        project_id,
        user_uid,
        offset,
        limit,
    )
    tasks = session.execute(
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.owner_uid == user_uid,
            Task.status != TaskStatus.DONE.value,
        )
        .offset(offset)
        .limit(limit)
    )
    return tasks.scalars().all()


def _get_ai_comments_for_task(task: Task) -> dict:
    """
    Вызываем внешний AI сервис для обзора задачи.
    """
    request = f"Дай комментарий к задаче {task.name}"
    return {"request", request}



async def get_active_comment_by_task_id(
    db: AsyncSession, task_id: int, user_uid: str
) -> AIReview:
    """
    Получаем активный AI комментарий для задачи по её ID.
    """

    result = await db.execute(
        select(AIReview).filter(
            AIReview.task_id == task_id,
            AIReview.is_active,
            AIReview.owner_uid == user_uid,  # noqa: E712
        )
    )

    ret = result.scalars().first()
    print(f"Итог {ret}")
    return ret


async def get_all_comments_for_task(
    db: AsyncSession, task_id: int, user_uid: str
) -> Sequence[AIReview]:
    """
    Получаем все комментарии по задаче
    """

    result = await db.execute(
        select(AIReview).filter(
            AIReview.task_id == task_id,
            AIReview.owner_uid == user_uid,  # noqa: E712
        )
    )

    return result.scalars().all()
