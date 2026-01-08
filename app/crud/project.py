from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
from app.schemas import ProjectCreate


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


async def get_projects(db: AsyncSession, user_uid: str) -> Sequence[Project]:
    result = await db.execute(select(Project).filter(Project.owner_uid == user_uid))
    return result.scalars().all()
