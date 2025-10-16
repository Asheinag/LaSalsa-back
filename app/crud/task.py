from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import ProjectStatus, ProjectType, TaskStatus
from app.crud.project import create_project, get_project_by_id, get_project_by_name
from app.models import Task
from app.schemas import ProjectCreate, TaskCreate


def validate_owner(user_uid: str, task: Task) -> bool:
    """Check if the task belongs to the user."""
    return task.owner_uid == user_uid


async def create_task(db: AsyncSession, task: TaskCreate, user_uid: str) -> Task:
    project_id = task.project_id
    project_name = task.project_name
    project = None

    if project_id:
        project = await get_project_by_id(db, project_id, user_uid)

    if project_name:
        project = await get_project_by_name(db, project_name, user_uid)
        if not project:
            project = await create_project(
                db,
                ProjectCreate(
                    name=project_name,
                    status=ProjectStatus.INACTIVE,
                    type=ProjectType.LIST,
                    description=None,
                    deadline=None,
                ),
                user_uid,
            )

    db_task = Task(
        name=task.name,
        description=task.description,
        planned_at=task.planned_at,
        created_at=datetime.now(),
        status=task.status.value
        if isinstance(task.status, TaskStatus)
        else task.status,
        closed_at=task.closed_at,
        project_id=project.id if project else None,
        owner_uid=user_uid,
        parent_id=task.parent_id,
    )

    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def get_tasks_by_offset(
    db: AsyncSession, user_uid: str, offset: int = 0, limit: int = 100
) -> Sequence[Task]:
    """Retrieve tasks for a user with pagination."""
    result = await db.execute(
        select(Task).where(Task.owner_uid == user_uid).offset(offset).limit(limit)
    )

    return result.scalars().all()


async def get_task_by_id(db: AsyncSession, task_id: int, user_uid: str) -> Task | None:
    """Retrieve a task by its ID and user UID.
    Returns None if the task does not exist or does not belong to the user."""
    task = await db.get(Task, task_id)
    if not task:
        return None
    if not validate_owner(user_uid, task):
        return None
    return task


async def delete_task(db: AsyncSession, task_id: int, user_uid: str) -> Task | None:
    task = await db.get(Task, task_id)
    if not task:
        return None
    if not validate_owner(user_uid, task):
        return None

    await db.delete(task)
    await db.commit()
    return task


async def update_task(
    db: AsyncSession, task_id: int, task_data: TaskCreate, user_uid: str
) -> Task | None:
    task = await db.get(Task, task_id)
    if not task:
        return None
    if not validate_owner(user_uid, task):
        return None

    task.name = task_data.name
    task.description = task_data.description
    task.planned_at = task_data.planned_at
    task.closed_at = task_data.closed_at
    task.status = (
        task_data.status.value
        if isinstance(task_data.status, TaskStatus)
        else task_data.status
    )
    task.project_id = task_data.project_id
    task.parent_id = task_data.parent_id
    await db.commit()
    await db.refresh(task)
    return task


async def update_task_status(
    db: AsyncSession, task_id: int, status: TaskStatus, user_uid: str
) -> Task | None:
    task = await db.get(Task, task_id)
    if not task:
        return None
    if not validate_owner(user_uid, task):
        return None
    task.status = status.value
    if status == TaskStatus.DONE:
        task.closed_at = datetime.now()
    else:
        task.closed_at = None
    await db.commit()
    await db.refresh(task)
    return task


async def get_tasks_by_project_id(
    db: AsyncSession, project_id: int, user_uid: str, offset: int = 0, limit: int = 100
) -> Sequence[Task]:
    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id, Task.owner_uid == user_uid)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def get_task_children(
    db: AsyncSession, task_id: int, user_uid: str
) -> Sequence[Task]:
    task = await get_task_by_id(db, task_id, user_uid)
    if not task:
        return []

    current_task = task
    result = await db.execute(
        select(Task).where(
            Task.parent_id == current_task.id, Task.owner_uid == user_uid
        )
    )
    result = result.scalars().all()
    return result


async def get_tasks_today(
    db: AsyncSession, user_uid: str, offset: int = 0, limit: int = 100
) -> Sequence[Task]:
    today = datetime.now().date()
    result = await db.execute(
        select(Task)
        .where(
            Task.planned_at != None,  # noqa: E711
            Task.planned_at >= datetime.combine(today, datetime.min.time()),
            Task.planned_at <= datetime.combine(today, datetime.max.time()),
            Task.owner_uid == user_uid,
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def get_tasks_later(
    db: AsyncSession, user_uid: str, offset: int = 0, limit: int = 100
) -> Sequence[Task]:
    today = datetime.now().date()
    result = await db.execute(
        select(Task)
        .where(
            Task.planned_at != None,  # noqa: E711
            Task.planned_at > datetime.combine(today, datetime.max.time()),
            Task.owner_uid == user_uid,
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()
