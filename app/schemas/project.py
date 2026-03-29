from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.common import ProjectStatus, ProjectType


# Это базовая модель проекта, которая включает только общие поля, которые могут быть полезны для отображения списка проектов
class ProjectBase(BaseModel):
    name: str = Field(..., title="Project Name", description="Name of the project")
    id: int = Field(
        ..., title="Project ID", description="Unique identifier for the project"
    )
    status: ProjectStatus = Field(
        ProjectStatus.ACTIVE,
        title="Project Status",
        description="Current status of the project",
    )
    owner_uid: str = Field(
        ..., title="Owner UID", description="Unique identifier for the project owner"
    )
    color_id: Optional[int] = Field(
        None, title="Color ID", description="Color identifier for the project"
    )


# Это модель для создания проекта, которая включает только необходимые поля для создания
class ProjectCreate(BaseModel):
    name: str = Field(..., title="Project Name", description="Name of the project")
    status: ProjectStatus = Field(
        ProjectStatus.ACTIVE,
        title="Project Status",
        description="Current status of the project",
    )
    type: ProjectType = Field(
        ProjectType.LIST, title="Project Type", description="Type of the project"
    )
    description: Optional[str] = Field(
        None, title="Project Description", description="Description of the project"
    )
    deadline: Optional[datetime] = Field(
        None, title="Deadline", description="Deadline for the project"
    )
    color_id: Optional[int] = Field(
        None, title="Color ID", description="Color identifier for the project"
    )


# Это модель для отображения проекта, которая включает все поля, включая те, которые не нужны при создании
class ProjectRead(ProjectBase):
    description: Optional[str] = Field(
        None, title="Project Description", description="Description of the project"
    )
    created_at: datetime = Field(
        ..., title="Created At", description="Timestamp when the project was created"
    )
    deadline: Optional[datetime] = Field(
        None, title="Deadline", description="Deadline for the project"
    )
    type: ProjectType = Field(
        ProjectType.LIST, title="Project Type", description="Type of the project"
    )
    color_id: Optional[int] = Field(
        None, title="Color ID", description="Color identifier for the project"
    )
    updated_at: Optional[datetime] = Field(
        None, title="Updated At", description="Timestamp when the project was updated"
    )
    parent_id: Optional[int] = Field(
        None, title="Parent ID", description="ID of the parent project"
    )


# Это модель для обновления проекта, которая позволяет обновлять только определенные поля
class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(
        None, title="Project Name", description="Name of the project"
    )
    status: Optional[ProjectStatus] = Field(
        None, title="Project Status", description="Current status of the project"
    )
    type: Optional[ProjectType] = Field(
        None, title="Project Type", description="Type of the project"
    )
    description: Optional[str] = Field(
        None, title="Project Description", description="Description of the project"
    )
    deadline: Optional[datetime] = Field(
        None, title="Deadline", description="Deadline for the project"
    )
    color_id: Optional[int] = Field(
        None, title="Color ID", description="Color identifier for the project"
    )


# Это модель для отображения статистики проекта
class ProjectStats(BaseModel):
    total: int = Field(
        ..., title="Total Tasks", description="Total number of tasks in the project"
    )
    completed: int = Field(
        ...,
        title="Completed Tasks",
        description="Number of completed tasks in the project",
    )
    active: int = Field(
        ..., title="Active Tasks", description="Number of active tasks in the project"
    )
