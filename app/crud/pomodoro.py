from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Pomodoro, Task
from app.schemas import PomodoroCreate, PomodoroUpdate


def validate_owner(user_uid: str, pomodoro: Pomodoro) -> bool:
    return pomodoro.owner_uid == user_uid


async def create_pomodoro(
    db: AsyncSession, pomodoro: PomodoroCreate, user_uid: str
) -> Pomodoro:
    db_pomodoro = Pomodoro(
        note=pomodoro.note,
        owner_uid=user_uid,
        duration_minutes=pomodoro.duration_minutes,
        previous_pomodoro_id=pomodoro.previous_pomodoro_id,
    )
    db.add(db_pomodoro)
    await db.commit()
    await db.refresh(db_pomodoro)
    return db_pomodoro


async def get_pomodoro(
    db: AsyncSession, pomodoro_id: int, user_uid: int
) -> Pomodoro | None:
    result = await db.get(Pomodoro, pomodoro_id)
    if not result or not validate_owner(user_uid, result):
        return None
    return result


async def get_pomodoro_tasks(
    db: AsyncSession, pomodoro_id: int, user_uid: str
) -> Sequence[Task]:
    result = await db.execute(
        select(Task).where(Task.pomodoro_id == pomodoro_id, Task.owner_uid == user_uid)
    )
    tasks = result.scalars().all()
    return tasks


async def delete_pomodoro(db: AsyncSession, pomodoro_id: int, user_uid: int) -> None:
    result = await db.get(Pomodoro, pomodoro_id)
    if not result or not validate_owner(user_uid, result):
        return None

    await db.delete(result)
    await db.commit()


async def update_pomodoro(
    db: AsyncSession, pomodoro_id: int, pomodoro_update: PomodoroUpdate, user_uid: str
) -> Pomodoro | None:
    result = await db.get(Pomodoro, pomodoro_id)
    if not result or not validate_owner(user_uid, result):
        return None

    if pomodoro_update.note is not None:
        result.note = pomodoro_update.note

    if pomodoro_update.duration_minutes is not None:
        result.duration_minutes = pomodoro_update.duration_minutes

    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result
