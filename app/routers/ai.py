from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_active_comment_by_task_id,
    get_all_comments_for_task,
    make_ai_tasks_review,
)
from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import TaskAIComment

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/review")
async def review_tasks_endpoint(
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """
    Эндпоинт для обзора задач с помощью ИИ
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = make_ai_tasks_review.delay(user_uid)
    return {"celery_task_id": result.id, "status": "AI Review started"}


@router.get("/review/status/{celery_task_id}")
async def get_review_tasks_status(
    celery_task_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """
    Эндпоинт для получения статуса задачи обзора задач с помощью ИИ
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = make_ai_tasks_review.AsyncResult(celery_task_id)
    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "done", "data": result.result}
    elif result.state == "FAILURE":
        return {"status": "error", "reason": str(result.result)}
    else:
        return {"status": result.state}


@router.get("/review/{task_id}", response_model=TaskAIComment)
async def get_ai_comment_by_task_endpoint(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> TaskAIComment:
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")

    return await get_active_comment_by_task_id(db, task_id, user_uid)


@router.get("/review/{task_id}/all", response_model=list[TaskAIComment])
async def get_all_comments_for_task_enpoint(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> list[TaskAIComment]:
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")

    return await get_all_comments_for_task(db, task_id, user_uid)
