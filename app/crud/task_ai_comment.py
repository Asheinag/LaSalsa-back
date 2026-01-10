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
from app.models import Task, TaskAIComment

logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.make_ai_tasks_review")
def make_ai_tasks_review(user_uid: str) -> dict[str, Any]:
    """
    Фоновая задача для обзора задач с помощью ИИ.
    """
    with get_sync_session() as session:
        # Получаем задачи пользователя по 50 штук и передаем их в функцию получения комментариев от ИИ
        offset = 0
        limit = 50
        tasks = _collect_tasks_for_ai_review(session, user_uid, offset, limit)
        ai_comments_count = 0
        while tasks:
            ai_comments_dict = _get_ai_comments_for_tasks(tasks)
            for ai_comment_task_index in ai_comments_dict.keys():
                task_id = ai_comment_task_index
                comment_text = ai_comments_dict[ai_comment_task_index]

                # Выставляем старые AI комментарии
                deactivate_query = (
                    update(TaskAIComment)
                    .where(TaskAIComment.task_id == task_id)
                    .values(is_active=False)
                )
                session.execute(deactivate_query)

                # Создаем новый AI комментарий для задачи
                db_comment = TaskAIComment(
                    comment=comment_text,
                    created_at=datetime.now(),
                    task_id=task_id,
                    is_active=True,
                    owner_uid=user_uid,
                )
                session.add(db_comment)

            session.commit()
            ai_comments_count += len(ai_comments_dict)
            offset += limit
            tasks = _collect_tasks_for_ai_review(session, user_uid, offset, limit)

    return {"status": "done", "ai_comments_created": ai_comments_count}


def _collect_tasks_for_ai_review(
    session: Session,
    user_uid: str,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[Task]:
    """
    Собираем задачи пользователя для обзора ИИ.
    """
    logger.info(
        "Collecting tasks for AI review for user_uid=%s, offset=%d, limit=%d",
        user_uid,
        offset,
        limit,
    )
    tasks = session.execute(
        select(Task)
        .where(
            Task.owner_uid == user_uid,
            Task.status != TaskStatus.DONE.value,
        )
        .offset(offset)
        .limit(limit)
    )
    return tasks.scalars().all()


def _get_ai_comments_for_tasks(tasks: Sequence[Task]) -> dict:
    """
    Вызываем внешний AI сервис для обзора задач.
    """
    ai_comments_dict = {}
    for task in tasks:
        # Здесь должен быть вызов к реальному AI сервису
        ai_comments_dict[task.id] = f"AI review comment for task {task.name}"
    return ai_comments_dict


async def get_active_comment_by_task_id(
    db: AsyncSession, task_id: int, user_uid: str
) -> TaskAIComment:
    """
    Получаем активный AI комментарий для задачи по её ID.
    """

    result = await db.execute(
        select(TaskAIComment).filter(
            TaskAIComment.task_id == task_id,
            TaskAIComment.is_active,
            TaskAIComment.owner_uid == user_uid,  # noqa: E712
        )
    )

    ret = result.scalars().first()
    print(f"Итог {ret}")
    return ret


async def get_all_comments_for_task(
    db: AsyncSession, task_id: int, user_uid: str
) -> Sequence[TaskAIComment]:
    """
    Получаем все комментарии по задаче
    """

    result = await db.execute(
        select(TaskAIComment).filter(
            TaskAIComment.task_id == task_id,
            TaskAIComment.owner_uid == user_uid,  # noqa: E712
        )
    )

    return result.scalars().all()
