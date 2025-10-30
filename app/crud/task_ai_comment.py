from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TaskAIComment
from app.schemas import TaskAICommentBase


async def create_task_ai_comment(
    db: AsyncSession, comment: TaskAICommentBase, task_id: int
) -> TaskAIComment:
    db_comment = TaskAIComment(
        comment=comment.comment,
        created_at=datetime.now(),
        task_id=task_id,
        is_active=True,
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment


async def get_active_comments_by_task_id(
    db: AsyncSession, task_id: int
) -> Sequence[TaskAIComment]:
    result = await db.execute(
        select(TaskAIComment).filter(
            TaskAIComment.task_id == task_id,
            TaskAIComment.is_active == True,  # noqa: E712
        )
    )
    comments = result.scalars().all()
    return comments


async def deactivate_all_previous_comments(
    db: AsyncSession, task_id: int
) -> None:
    result = await db.execute(
        select(TaskAIComment).filter(
            TaskAIComment.task_id == task_id,
            TaskAIComment.is_active == True,  # noqa: E712
        )
    )
    comments = result.scalars().all()
    for comment in comments:
        comment.is_active = False
    await db.commit()
