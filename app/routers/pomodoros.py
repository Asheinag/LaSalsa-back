from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_pomodoro,
    delete_pomodoro,
    get_pomodoro,
    get_pomodoro_tasks,
    update_pomodoro,
)
from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import PomodoroCreate, PomodoroRead, PomodoroUpdate, TaskShort

router = APIRouter(prefix="/pomodoros", tags=["pomodoros"])


@router.post("/", response_model=PomodoroRead, status_code=201)
async def create_pomodoro_endpoint(
    pomodoro: PomodoroCreate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Создать новую сессию Pomodoro.
    """
    user_uid = user.get("uid")

    pomodoro = await create_pomodoro(db, pomodoro, user_uid)
    return pomodoro


@router.get("/{pomodoro_id}", response_model=PomodoroRead)
async def get_pomodoro_endpoint(
    pomodoro_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Получить сессию Pomodoro по её ID.
    """
    user_uid = user.get("uid")
    pomodoro = await get_pomodoro(db, pomodoro_id, user_uid)

    if not pomodoro:
        raise HTTPException(status_code=404, detail="Pomodoro not found")

    return pomodoro


@router.get("/{pomodoro_id}/tasks", response_model=list[TaskShort])
async def get_pomodoro_tasks_endpoint(
    pomodoro_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Получить задачи, связанные с сессией Pomodoro по её ID.
    """
    user_uid = user.get("uid")
    pomodoro_tasks = await get_pomodoro_tasks(db, pomodoro_id, user_uid)
    if not pomodoro_tasks:
        raise HTTPException(status_code=404, detail="Pomodoro not found")

    return pomodoro_tasks


@router.delete("/{pomodoro_id}", status_code=204)
async def delete_pomodoro_endpoint(
    pomodoro_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Удалить сессию Pomodoro по её ID.
    """
    user_uid = user.get("uid")
    pomodoro = await get_pomodoro(db, pomodoro_id, user_uid)
    if not pomodoro:
        raise HTTPException(status_code=404, detail="Pomodoro not found")

    await delete_pomodoro(db, pomodoro_id, user_uid)
    return Response(status_code=204)


@router.patch("/{pomodoro_id}", response_model=PomodoroRead)
async def update_pomodoro_endpoint(
    pomodoro_id: int,
    pomodoro_update: PomodoroUpdate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Обновить заметку сессии Pomodoro по её ID.
    """
    user_uid = user.get("uid")
    pomodoro = await update_pomodoro(db, pomodoro_id, pomodoro_update, user_uid)
    if not pomodoro:
        raise HTTPException(status_code=404, detail="Pomodoro not found")

    return pomodoro
