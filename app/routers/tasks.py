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
    get_task_childs,
    build_task_chain,

)
from app.schemas import TaskCreate, TaskRead, TaskShort, TaskStatusUpdate
from app.dependencies import verify_firebase_token
from celery.result import AsyncResult
from app.celery_app import celery_app



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


@router.get("/", response_model=list[TaskShort])
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


@router.delete("/{task_id}/")
async def delete_task_endpoint(
    task_id: int, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Delete a task by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    return await delete_task(db, task_id, user_uid)


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
    task_status: TaskStatusUpdate, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
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


@router.get("/{task_id}/childs/", response_model=list[TaskRead])
async def get_chain_tasks_endpoint(
    task_id: int, db: AsyncSession = Depends(get_async_session), user = Depends(verify_firebase_token)
):
    """
    Get all tasks in the chain of a given task.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_uid = user.get("uid")
    tasks = await get_task_childs(db, task_id, user_uid)
    return tasks


@router.post("/build_chain/{task_id}")
async def build_chain_endpoint(task_id: int, user = Depends(verify_firebase_token)):
    """
    Build a task chain for a given task ID.
    This is an asynchronous operation that can be processed by Celery.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    result = build_task_chain.delay(task_id) # type: ignore
    return {"celery_task_id": result.id, "status": "Task chain building started"}


@router.get("/build_chain/status/{celery_task_id}")
async def get_chain_status_endpoint(celery_task_id: str, user = Depends(verify_firebase_token)):
    """
    Get the status of the task chain building operation.
    """

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = AsyncResult(celery_task_id, app=celery_app)
    
    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "done", "data": result.result}
    elif result.state == "FAILURE":
        return {"status": "error", "reason": str(result.result)}
    else:
        return {"status": result.state}