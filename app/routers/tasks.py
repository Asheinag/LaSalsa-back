from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.crud import (
    create_task,
    get_tasks_by_offset,
    delete_task,
    update_task,
    update_task_status,
    get_task_by_id,
)
from app.schemas import TaskCreate, TaskRead, TaskShort, TaskStatus, TaskID
from app.dependencies import verify_firebase_token


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", status_code=201, response_model=TaskRead)
async def create_task_endpoint(
    task: TaskCreate, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Create a new task.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    return await create_task(db, task, user_uid)


@router.get("", response_model=list[TaskShort])
async def get_tasks_endpoint(
    offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Get tasks with pagination.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    return await get_tasks_by_offset(db, user_uid, offset, limit)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_by_id_endpoint(
    task_id: int, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Get a task by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    task = await get_task_by_id(db, task_id, user_uid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("")
async def delete_task_endpoint(
    task_id: TaskID, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Delete a task by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    return await delete_task(db, task_id.id, user_uid)


@router.put("/{task_id}/update", response_model=TaskRead)
async def update_task_endpoint(
    task_id: int, task_data: TaskCreate, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Update a task by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    task = await update_task(db, task_id, task_data, user_uid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/status", response_model=TaskRead)
async def update_task_status_endpoint(
    task_status: TaskStatus, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Update the status of a task by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    task = await update_task_status(db, task_status.id, task_status.status, user_uid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
