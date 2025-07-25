from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_project,
    get_project_by_id,
    get_projects,
    get_tasks_by_project_id,
)
from app.database import get_async_session
from app.dependencies import verify_firebase_token
from app.schemas import ProjectBase, ProjectCreate, ProjectRead, TaskShort

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectBase])
async def get_projects_endpoint(
    db: AsyncSession = Depends(get_async_session), user=Depends(verify_firebase_token)
):  # noqa: B008
    """
    Get a list of projects.
    """
    user_uid = user.get("uid")
    projects = await get_projects(db, user_uid)
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")

    return projects


@router.get("/{project_id}/tasks", response_model=list[TaskShort])
async def get_tasks_by_project_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Get tasks by project ID.
    """
    user_uid = user.get("uid")
    tasks = await get_tasks_by_project_id(db, project_id, user_uid)
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found for this project")

    return tasks


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project_by_id_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Get a project by its ID.
    """
    user_uid = user.get("uid")
    project = await get_project_by_id(db, project_id, user_uid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.post("/", response_model=ProjectBase, status_code=201)
async def create_project_endpoint(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(verify_firebase_token),  # noqa: B008
):
    """
    Create a new project
    """
    user_uid = user.get("uid")
    new_project = await create_project(db, project, user_uid)
    if not new_project:
        raise HTTPException(status_code=400, detail="Failed to create project")

    return new_project
