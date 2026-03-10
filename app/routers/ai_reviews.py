from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import get_celery_task_status
from app.crud import (
    get_all_comments,
    get_last_active_review,
    get_review_by_id,
    run_project_review,
    run_task_review,
)
from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import AIReviewRead, AIReviewShort

# from app.schemas import TaskAIComment

router = APIRouter(prefix="/ai-reviews", tags=["ai-reviews"])


@router.post("/tasks/{task_id}/run")
async def run_task_review_endpoint(
    task_id: int,
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """
    Эндпоинт для старта получения AI ревью по задаче
    Возвращает ID задачи Celery по которой можно будет получить АИ ревью
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = run_task_review.delay(user_uid, task_id)

    return {"celery_task_id": result.id, "status": f"Task {task_id} AI review started"}


@router.post("/projects/{project_id}/run")
async def run_project_review_endpoint(
    project_id: int,
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """
    Эндпоинт для старта получения AI ревью по проекту
    Возвращает ID задачи Celery по которой можно будет получить АИ ревью
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = run_project_review.delay(user_uid, project_id)

    return {
        "celery_task_id": result.id,
        "status": f"Project {project_id} AI review started",
    }


@router.get("/status/{celery_task_id}")
async def get_ai_review_status_endpoint(
    celery_task_id: str, user: dict[str, Any] = Depends(verify_firebase_token)
) -> dict[str, Any]:  # noqa: B008
    """
    Эндпоинт для запроса статуса задачи поставленной на Celery
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return get_celery_task_status(celery_task_id)


@router.get("/tasks/{task_id}/active", response_model=AIReviewRead)
async def get_active_review_by_task_id_endpoint(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> AIReviewRead:
    """
    Эндпоинт для получения текущего активного комментария к задаче
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = await get_last_active_review(db, user_uid, task_id=task_id)

    if not result:
        raise HTTPException(status_code=404, detail="AIReview not found")
    return result


@router.get("/tasks/{task_id}/history", response_model=list[AIReviewShort])
async def get_history_review_by_task_id_endpoint(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> list[AIReviewShort]:
    """
    Эндпоинт для получения списка всех и активных и нет комментариев по задаче
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    history = await get_all_comments(db, user_uid, task_id=task_id)

    return history


@router.get("/{review_id}", response_model=AIReviewRead)
async def get_review_by_id_endpoint(
    review_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> AIReviewRead:
    """
    Эндпоинт получения ревью по его ID
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    review = await get_review_by_id(db, review_id, user_uid)

    return review


@router.get("/projects/{project_id}/active", response_model=AIReviewRead)
async def get_active_review_by_project_id_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> AIReviewRead:
    """
    Эндпоинт для получения текущего активного комментария к задаче
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = await get_last_active_review(db, user_uid, project_id=project_id)

    if not result:
        raise HTTPException(status_code=404, detail="AIReview not found")
    return result


@router.get("/projects/{project_id}/history", response_model=list[AIReviewShort])
async def get_history_review_by_project_id_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> list[AIReviewShort]:
    """
    Эндпоинт для получения списка всех и активных и нет комментариев по задаче
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    history = await get_all_comments(db, user_uid, project_id=project_id)

    return history
