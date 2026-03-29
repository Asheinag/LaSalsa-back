from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import ProjectStatus, TaskStatus
from app.models import Project, Task
from app.schemas import ProjectCreate, ProjectUpdate


def validate_owner(user_uid: str, project: Project) -> bool:
    return project.owner_uid == user_uid


async def create_project(
    db: AsyncSession, project: ProjectCreate, user_uid: str
) -> Project:
    db_project = Project(
        name=project.name,
        description=project.description,
        created_at=datetime.now(),
        type=project.type,
        deadline=project.deadline,
        status=project.status,
        owner_uid=user_uid,
        color_id=project.color_id,
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


async def get_project_by_id(
    db: AsyncSession, project_id: int, user_uid: str
) -> Project | None:
    project = await db.get(Project, project_id)
    if not project:
        return None
    if not validate_owner(user_uid, project):
        return None
    return project


async def get_project_by_name(
    db: AsyncSession, project_name: str, user_uid: str
) -> Project | None:
    result = await db.execute(select(Project).where(Project.name == project_name))
    project = result.scalars().first()

    if not project:
        return None

    if not validate_owner(user_uid, project):
        return None

    return project


async def get_projects(
    db: AsyncSession,
    user_uid: str,
    offset: int = 0,
    limit: int = 100,
    is_active: bool = True,
) -> Sequence[Project]:
    if is_active:
        result = await db.execute(
            select(Project)
            .where(
                Project.owner_uid == user_uid,
                Project.status.in_(
                    [ProjectStatus.ACTIVE.value, ProjectStatus.INACTIVE.value]
                ),
            )
            .offset(offset)
            .limit(limit)
        )
    else:
        result = await db.execute(
            select(Project)
            .where(
                Project.owner_uid == user_uid,
                Project.status.in_(
                    [ProjectStatus.CANCELLED.value, ProjectStatus.COMPLETED.value]
                ),
            )
            .offset(offset)
            .limit(limit)
        )
    return result.scalars().all()


async def update_project(
    db: AsyncSession, project_id: int, project_data: ProjectUpdate, user_uid: str
) -> Project | None:
    project = await get_project_by_id(db, project_id, user_uid)
    if not project:
        return None

    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key not in ["id", "owner_uid"]:
            setattr(project, key, value)

    project.updated_at = datetime.now()

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession, project_id: int, user_uid: str
) -> Project | None:
    project = await get_project_by_id(db, project_id, user_uid)
    if not project:
        return None

    if not validate_owner(user_uid, project):
        return None

    tasks = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = tasks.scalars().all()
    for task in tasks:
        task.project_id = None

    await db.delete(project)
    await db.commit()
    return project


async def get_project_stats(
    db: AsyncSession, project_id: int, user_uid: str
) -> dict[str, int] | None:
    project = await get_project_by_id(db, project_id, user_uid)
    if not project:
        return None

    total_tasks = await db.execute(select(Task).where(Task.project_id == project_id))
    total_tasks = total_tasks.scalars().all()
    total_tasks_count = len(total_tasks)

    completed_tasks_count = len(
        [task for task in total_tasks if task.status == TaskStatus.DONE.value]
    )

    active_tasks_count = len(
        [task for task in total_tasks if task.status == TaskStatus.TODO.value]
    )

    return {
        "total": total_tasks_count,
        "completed": completed_tasks_count,
        "active": active_tasks_count,
    }
