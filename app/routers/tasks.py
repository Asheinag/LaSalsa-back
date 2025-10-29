from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.crud import (
    build_task_chain,
    create_task,
    delete_task,
    full_update_task,
    get_task_by_id,
    get_task_children,
    get_tasks_by_offset,
    get_tasks_later,
    get_tasks_today,
    update_task,
)
from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import TaskCreate, TaskRead, TaskShort, TaskUpdate

# Определяем роутер для задач
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", status_code=201, response_model=TaskRead)
async def create_task_endpoint(
    task: TaskCreate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    СОздание новой задачи
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    return await create_task(db, task, user_uid)


@router.get("/", response_model=list[TaskShort])
async def get_tasks_endpoint(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Получение списка задач с пагинацией
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    return await get_tasks_by_offset(db, user_uid, offset, limit)


@router.get("/today", response_model=list[TaskShort])
async def get_tasks_today_endpoint(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Получение задач на сегодня с пагинацией
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_uid = user.get("uid")
    tasks = await get_tasks_today(db, user_uid, offset, limit)
    return tasks


@router.get("/later", response_model=list[TaskShort])
async def get_tasks_later_endpoint(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Получение задач на потом с пагинацией
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    return await get_tasks_later(db, user_uid, offset, limit)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_by_id_endpoint(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Получение задачи по ID
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    task = await get_task_by_id(db, task_id, user_uid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task_endpoint(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Удаление задачи по ID
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = await delete_task(db, task_id, user_uid)

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    return Response(status_code=204)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task_endpoint(
    task_id: int,
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Update a task by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    task = await full_update_task(db, task_id, task_data, user_uid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_tasks_field_endpoint(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Update specific fields of a task by ID.
    """

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    task = await update_task(db, task_id, task_data, user_uid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/children/", response_model=list[TaskRead])
async def get_chain_tasks_endpoint(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Get all tasks in the chain of a given task.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    tasks = await get_task_children(db, task_id, user_uid)
    return tasks


@router.post("/build_chain/{task_id}")
async def build_chain_endpoint(task_id: int, user=Depends(verify_firebase_token)):  # noqa: B008
    """
    Build a task chain for a given task ID.
    This is an asynchronous operation that can be processed by Celery.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = build_task_chain.delay(task_id)  # type: ignore
    return {"celery_task_id": result.id, "status": "Task chain building started"}


@router.get("/build_chain/status/{celery_task_id}")
async def get_chain_status_endpoint(
    celery_task_id: str, user=Depends(verify_firebase_token)
):  # noqa: B008
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
