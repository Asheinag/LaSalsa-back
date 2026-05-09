from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.common import TaskStatus
from app.database import get_sync_session
from app.models import RecurringTask, Task
from app.schemas import RecurringTaskCreate, RecurringTaskUpdate
from app.utils import calculate_next_run


async def create_recurring_task(
    db: AsyncSession, recurring_task: RecurringTaskCreate, user_uid: str
) -> RecurringTask:
    next_run_at = calculate_next_run(
        recurring_task.frequency,
        recurring_task.days,
        recurring_task.timezone,
        from_dt=datetime.now(UTC),
    )
    db_recurring_task = RecurringTask(
        **recurring_task.model_dump(),
        owner_uid=user_uid,
        next_run_at=next_run_at
    )
    db.add(db_recurring_task)
    await db.commit()
    await db.refresh(db_recurring_task)
    return db_recurring_task

async def get_recurring_task(db: AsyncSession, recurring_task_id: int) -> RecurringTask:
    return await db.get(RecurringTask, recurring_task_id)

async def get_recurring_tasks(db: AsyncSession, user_uid: str) -> list[RecurringTask]:
    return await db.execute(select(RecurringTask).where(RecurringTask.owner_uid == user_uid)).scalars().all()

async def update_recurring_task(
    db: AsyncSession, recurring_task_id: int, recurring_task: RecurringTaskUpdate
) -> RecurringTask:
    db_recurring_task = await get_recurring_task(db, recurring_task_id)
    if not db_recurring_task:
        raise Exception("Recurring task not found")
    for key, value in recurring_task.model_dump().items():
        setattr(db_recurring_task, key, value)
    await db.commit()
    return db_recurring_task

async def delete_recurring_task(db: AsyncSession, recurring_task_id: int) -> None:
    db_recurring_task = await get_recurring_task(db, recurring_task_id)
    if not db_recurring_task:
        raise Exception("Recurring task not found")
    await db.delete(db_recurring_task)
    await db.commit()

async def get_due_recurring_tasks(db: AsyncSession) -> list[RecurringTask]:
    return await db.execute(select(RecurringTask).where(RecurringTask.is_active, RecurringTask.next_run_at < datetime.now(UTC))).scalars().all()

async def get_recurring_task_by_task_id(db: AsyncSession, task_id: int) -> RecurringTask:
    return await db.get(RecurringTask, task_id)

@celery_app.task(name="app.tasks.process_recurring_tasks")
def process_recurring_tasks() -> None:
    """
    Запускается каждые 15 минут через Celery beat.
    Создаёт задачи для всех пользователей у которых наступил next_run_at.
    """
    with get_sync_session() as session:
        due = get_due_recurring_tasks(session)
        for template in due:
            # создать Task по шаблону
            task = Task(
                name=template.name,
                description=template.description,
                project_id=template.project_id,
                owner_uid=template.owner_uid,
                status=TaskStatus.TODO,
                recurring_task_id=template.id,  # помечаем что задача создана по шаблону
            )
            session.add(task)
            # обновить next_run_at и last_run_at
            template.last_run_at = datetime.now(UTC)
            template.next_run_at = calculate_next_run(
                template.frequency,
                template.days,
                template.timezone,
                from_dt=datetime.now(UTC),
            )
        session.commit()
