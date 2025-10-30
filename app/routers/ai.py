from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_tasks_by_offset
from app.database import get_async_session
from app.dependencies import verify_firebase_token

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/review-tasks")
def review_tasks_endpoint(db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token)):
    """
    Эндпоинт для обзора задач с помощью ИИ
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    response = get_tasks_by_offset(db, user_uid, 0, 100, active_only=True)
    task_list = []
    if not response:
        raise HTTPException(status_code=404, detail="No tasks found for review")
    while True:
        tasks = response.result()
        if not tasks:
            break
        task_list.extend(tasks)
        offset = len(task_list)
        response = get_tasks_by_offset(db, user_uid, offset, 100, active_only=True)

    return Response(content="AI task review endpoint is under construction.", status_code=200)
