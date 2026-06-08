from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_recurring_task,
    delete_recurring_task,
    get_recurring_task,
    get_recurring_tasks,
    update_recurring_task,
)
from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import RecurringTaskCreate, RecurringTaskRead, RecurringTaskUpdate

router = APIRouter(prefix="/recurring-tasks", tags=["recurring_tasks"])


@router.post("/", response_model=RecurringTaskRead, status_code=201)
async def create_recurring_task_endpoint(
    recurring_task: RecurringTaskCreate,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> RecurringTaskRead:
    """
    Create a recurring task
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_uid = user.get("uid")
    new_recurring_task = await create_recurring_task(db, recurring_task, user_uid)
    if not new_recurring_task:
        raise HTTPException(status_code=400, detail="Failed to create recurring task")
    return new_recurring_task


@router.get("/", response_model=list[RecurringTaskRead])
async def get_recurring_tasks_endpoint(
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> list[RecurringTaskRead]:
    """
    Get all recurring tasks by user
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_uid = user.get("uid")
    tasks = await get_recurring_tasks(db, user_uid)
    if not tasks:
        raise HTTPException(status_code=404, detail="No recurring tasks found")
    return tasks


@router.get("/{recurring_task_id}", response_model=RecurringTaskRead)
async def get_recurring_task_endpoint(
    recurring_task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> RecurringTaskRead:
    """
    Get a recurring task by id
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    recurring_task = await get_recurring_task(db, recurring_task_id, user.get("uid"))
    if not recurring_task:
        raise HTTPException(status_code=404, detail="Recurring task not found")
    return recurring_task


@router.patch("/{recurring_task_id}", response_model=RecurringTaskRead)
async def update_recurring_task_endpoint(
    recurring_task_id: int,
    recurring_task: RecurringTaskUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> RecurringTaskRead:
    """
    Update a fields of recurring task
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_uid = user.get("uid")
    updated_recurring_task = await update_recurring_task(
        db, recurring_task_id, recurring_task, user_uid
    )
    if not updated_recurring_task:
        raise HTTPException(status_code=404, detail="Recurring task not found")
    return updated_recurring_task


@router.delete("/{recurring_task_id}")
async def delete_recurring_task_endpoint(
    recurring_task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> str:
    """
    Delete a recurring task
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_uid = user.get("uid")
    deleted_recurring_task = await delete_recurring_task(
        db, recurring_task_id, user_uid
    )
    if not deleted_recurring_task:
        raise HTTPException(status_code=404, detail="Recurring task not found")
    return deleted_recurring_task
