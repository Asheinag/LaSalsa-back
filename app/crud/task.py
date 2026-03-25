from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import ProjectStatus, ProjectType, TaskStatus
from app.crud import (
    create_project,
    get_pomodoro,
    get_project_by_id,
    get_project_by_name,
)
from app.models import Task
from app.schemas import ProjectCreate, TaskCreate, TaskUpdate


def validate_owner(user_uid: str, task: Task) -> bool:
    """Check if the task belongs to the user."""
    return task.owner_uid == user_uid


async def create_task(db: AsyncSession, task: TaskCreate, user_uid: str) -> Task:
    project_id = task.project_id
    project_name = task.project_name
    project = None

    if project_id and project_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either project_id or project_name, not both.",
        )

    if project_id:
        project = await get_project_by_id(db, project_id, user_uid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project {project_id} not found, cannot assign task to it.",
            )

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
    db: AsyncSession,
    user_uid: str,
    offset: int = 0,
    limit: int = 100,
    is_active: bool = True,
) -> Sequence[Task]:
    """Retrieve tasks for a user with pagination."""

    if is_active:
        result = await db.execute(
            select(Task)
            .where(
                Task.owner_uid == user_uid,
                Task.status != TaskStatus.DONE.value,
            )
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
    else:
        result = await db.execute(
            select(Task)
            .where(
                Task.owner_uid == user_uid,
                Task.status == TaskStatus.DONE.value,
            )
            .offset(offset)
            .limit(limit)
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


async def full_update_task(
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

    if task_data.project_id is not None:
        project = await get_project_by_id(db, task_data.project_id, user_uid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project {task_data.project_id} not found, cannot assign task to it.",
            )
        else:
            task.project_id = project.id

    if task_data.pomodoro_id is not None:
        pomodoro = await get_pomodoro(db, task_data.pomodoro_id, user_uid)
        if not pomodoro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pomodoro {task_data.pomodoro_id} not found, cannot assign task to it.",
            )
        else:
            task.pomodoro_id = pomodoro.id

    if task_data.parent_id is not None:
        parent_task = await db.get(Task, task_data.parent_id)
        if not parent_task or not validate_owner(user_uid, parent_task):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent task {task_data.parent_id} not found, cannot assign as parent.",
            )
        else:
            task.parent_id = parent_task.id

    await db.commit()
    await db.refresh(task)
    return task


async def _update_task_simple_fields(task: Task, task_data: TaskUpdate) -> None:
    """Update basic task fields if they are provided."""
    if task_data.name is not None:
        task.name = task_data.name
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.closed_at is not None:
        task.closed_at = task_data.closed_at
    if "planned_at" in task_data.model_fields_set:
        task.planned_at = task_data.planned_at  # None или значение — оба варианта пишем
    elif task_data.planned_at is not None:
        task.planned_at = task_data.planned_at


async def _update_task_complex_fields(
    db: AsyncSession, task: Task, task_data: TaskUpdate, user_uid: str
) -> None:
    """Update complex task fields that require DB lookups."""
    if "project_id" in task_data.model_fields_set:
        if task_data.project_id is None:
            task.project_id = None  # отвязать от проекта
        else:
            project = await get_project_by_id(db, task_data.project_id, user_uid)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project {task_data.project_id} not found, cannot assign task to it.",
                )
            task.project_id = project.id

    if task_data.pomodoro_id is not None:
        pomodoro = await get_pomodoro(db, task_data.pomodoro_id, user_uid)
        if not pomodoro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pomodoro {task_data.pomodoro_id} not found, cannot assign task to it.",
            )
        task.pomodoro_id = pomodoro.id

    if task_data.parent_id is not None:
        parent_task = await db.get(Task, task_data.parent_id)
        if not parent_task or not validate_owner(user_uid, parent_task):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent task {task_data.parent_id} not found, cannot assign as parent.",
            )
        task.parent_id = parent_task.id


async def _update_task_status(
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


async def update_task(
    db: AsyncSession, task_id: int, task_data: TaskUpdate, user_uid: str
) -> Task | None:
    task = await db.get(Task, task_id)
    if not task or not validate_owner(user_uid, task):
        return None

    await _update_task_simple_fields(task, task_data)
    await _update_task_complex_fields(db, task, task_data, user_uid)
    if task_data.status is not None:
        await _update_task_status(db, task_id, task_data.status, user_uid)
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
    db: AsyncSession, user_uid: str, timezone: str = "UTC", offset: int = 0, limit: int = 100
) -> Sequence[Task]:
    now = datetime.now(ZoneInfo(timezone))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    print(f"Получаем задачи на сегодня для user_uid={user_uid} с offset={offset} и limit={limit}")
    print(f"Текущая дата: {now}, начало дня: {start}, конец дня: {end}")
    result = await db.execute(
        select(Task)
        .where(
            Task.planned_at != None,  # noqa: E711
            Task.planned_at >= start,
            Task.planned_at <= end,
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
