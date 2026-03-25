from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_project,
    delete_project,
    get_project_by_id,
    get_project_stats,
    get_projects,
    get_tasks_by_project_id,
    update_project,
)
from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import (
    ProjectBase,
    ProjectCreate,
    ProjectRead,
    ProjectStats,
    ProjectUpdate,
    TaskShort,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectBase])
async def get_projects_endpoint(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
    is_active: bool = True,
) -> list[ProjectBase]:  # noqa: B008
    """
    Get a list of projects.
    """
    print(f"Получен запрос на получение проектов с offset={offset} и limit={limit}, is_active={is_active}")
    user_uid = user.get("uid")
    projects = await get_projects(db, user_uid, offset, limit, is_active)
    return projects


@router.get("/{project_id}/tasks", response_model=list[TaskShort])
async def get_tasks_by_project_endpoint(
    project_id: int,
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> list[TaskShort]:
    """
    Get tasks by project ID.
    """
    user_uid = user.get("uid")
    tasks = await get_tasks_by_project_id(db, project_id, user_uid, offset, limit)
    return tasks


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project_by_id_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> ProjectRead:
    """
    Get a project by its ID.
    """
    user_uid = user.get("uid")
    project = await get_project_by_id(db, project_id, user_uid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> ProjectStats:
    """
    Get statistics for a project by its ID.
    """
    user_uid = user.get("uid")
    stats = await get_project_stats(db, project_id, user_uid)
    if not stats:
        raise HTTPException(status_code=404, detail="Project not found")

    return stats


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project_endpoint(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> ProjectRead:
    """
    Create a new project
    """
    user_uid = user.get("uid")
    new_project = await create_project(db, project, user_uid)
    if not new_project:
        raise HTTPException(status_code=400, detail="Failed to create project")

    return new_project


@router.patch("/{project_id}", response_model=ProjectRead, status_code=200)
async def update_project_endpoint(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),  # noqa: B008
) -> ProjectRead:
    """
    Update a project by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    project = await update_project(db, project_id, project_data, user_uid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: dict[str, Any] = Depends(verify_firebase_token),
) -> Response:  # noqa: B008
    """
    Delete a project by ID.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_uid = user.get("uid")
    result = await delete_project(db, project_id, user_uid)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")

    return Response(status_code=204)
