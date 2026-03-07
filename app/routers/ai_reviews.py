from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException

from app.celery_app import celery_app

# from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import (
    run_task_review,
)

# from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import TaskAIReviewRead

# from app.schemas import TaskAIComment

router = APIRouter(prefix="/ai-reviews", tags=["ai-reviews"])


@router.post("/tasks/{task_id}/run")
async def run_task_review_endpoint(
    task_id: int,
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> dict[str, Any]:
    """
    Эндпоинт для старта получения AI ревью
    Возвращает ID задачи Celery по которой можно будет получить АИ ревью
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = run_task_review.delay(user_uid, task_id)
    return {"celery_task_id": result.id, "status": f"Task {task_id} AI review started"}


@router.get("/status/{celery_task_id}")
async def get_chain_status_endpoint(
    celery_task_id: str, user: dict[str, Any] = Depends(verify_firebase_token)
) -> dict[str, Any]:  # noqa: B008
    """
    Возвращает статус задачи поставленной на Celery
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

@router.get("/tasks/{task_id}/active", response_model=TaskAIReviewRead)
def get_active_review_by_task_id_endpoint(task_id: int, user:dict[str, Any] = Depends(verify_firebase_token)) -> TaskAIReviewRead:
    pass
