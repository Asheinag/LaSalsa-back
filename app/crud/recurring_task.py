import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.common import TaskStatus
from app.database import get_sync_session
from app.models import RecurringTask, Task
from app.schemas import RecurringTaskCreate, RecurringTaskUpdate
from app.utils import calculate_next_run, normalize_frequency

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def create_recurring_task(
    db: AsyncSession, recurring_task: RecurringTaskCreate, user_uid: str
) -> RecurringTask:
    frequency, days = normalize_frequency(recurring_task.frequency, recurring_task.days)
    next_run_at = calculate_next_run(
        frequency,
        days,
        recurring_task.timezone,
        from_dt=datetime.now(UTC),
    )
    recurring_task_data = recurring_task.model_dump()
    recurring_task_data["frequency"] = frequency
    recurring_task_data["days"] = days
    db_recurring_task = RecurringTask(
        **recurring_task_data, owner_uid=user_uid, next_run_at=next_run_at
    )
    db.add(db_recurring_task)
    await db.commit()
    await db.refresh(db_recurring_task)
    return db_recurring_task


async def get_recurring_task(
    db: AsyncSession, recurring_task_id: int, user_uid: str
) -> RecurringTask:
    result = await db.get(RecurringTask, recurring_task_id)
    if not result:
        return None
    if result.owner_uid != user_uid:
        return None
    return result


async def get_recurring_tasks(
    db: AsyncSession, user_uid: str
) -> Sequence[RecurringTask]:
    result = await db.execute(
        select(RecurringTask).where(RecurringTask.owner_uid == user_uid)
    )
    return result.scalars().all()


async def update_recurring_task(
    db: AsyncSession,
    recurring_task_id: int,
    recurring_task: RecurringTaskUpdate,
    user_uid: str,
) -> RecurringTask:
    db_recurring_task = await get_recurring_task(db, recurring_task_id, user_uid)
    if db_recurring_task.owner_uid != user_uid:
        return None
    need_calculate_next_run = False
    if not db_recurring_task:
        return None
    if recurring_task.name:
        db_recurring_task.name = recurring_task.name
    if recurring_task.description:
        db_recurring_task.description = recurring_task.description
    if recurring_task.project_id:
        db_recurring_task.project_id = recurring_task.project_id
    if recurring_task.frequency:
        db_recurring_task.frequency = recurring_task.frequency
        need_calculate_next_run = True
    if recurring_task.days:
        db_recurring_task.days = recurring_task.days
        need_calculate_next_run = True
    if recurring_task.timezone:
        db_recurring_task.timezone = recurring_task.timezone
        need_calculate_next_run = True
    if need_calculate_next_run:
        frequency, days = normalize_frequency(
            db_recurring_task.frequency, db_recurring_task.days
        )
        db_recurring_task.next_run_at = calculate_next_run(
            frequency,
            days,
            db_recurring_task.timezone,
            from_dt=datetime.now(UTC),
        )

    await db.commit()
    return db_recurring_task


async def delete_recurring_task(
    db: AsyncSession, recurring_task_id: int, user_uid: str
) -> None:
    db_recurring_task = await get_recurring_task(db, recurring_task_id, user_uid)
    if not db_recurring_task:
        return None
    if db_recurring_task.owner_uid != user_uid:
        return None
    await db.delete(db_recurring_task)
    await db.commit()


async def get_due_recurring_tasks(db: AsyncSession) -> list[RecurringTask]:
    result = await db.execute(
        select(RecurringTask).where(
            RecurringTask.is_active, RecurringTask.next_run_at < datetime.now(UTC)
        )
    )
    return result.scalars().all()


@celery_app.task(name="app.tasks.process_recurring_tasks")
def process_recurring_tasks() -> None:
    """
    Запускается каждые 15 минут через Celery beat.
    Создаёт задачи для всех пользователей у которых наступил next_run_at.
    """
    logger.debug("process_recurring_tasks")
    with get_sync_session() as session:
        due = (
            session.query(RecurringTask)
            .filter(RecurringTask.next_run_at < datetime.now(UTC))
            .all()
        )
        logger.debug(f"due: {due}")
        for template in due:
            # создать Task по шаблону
            logger.debug(f"template: {template}")
            task = Task(
                name=template.name,
                description=template.description,
                project_id=template.project_id,
                owner_uid=template.owner_uid,
                status=TaskStatus.TODO,
                planned_at=template.next_run_at,
                created_at=datetime.now(UTC),
                recurring_task_id=template.id,
            )
            logger.debug(f"task: {task}")
            session.add(task)
            # обновить next_run_at и last_run_at
            template.last_run_at = datetime.now(UTC)
            template.next_run_at = calculate_next_run(
                template.frequency,
                template.days,
                template.timezone,
                from_dt=datetime.now(UTC),
            )
            logger.debug(f"template: {template}")
        session.commit()
