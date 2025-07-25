from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.common import ProjectStatus, ProjectType


# This is a Pydantic model for the Project schema
class ProjectBase(BaseModel):
    name: str = Field(..., title="Project Name", description="Name of the project")
    id: int = Field(
        ..., title="Project ID", description="Unique identifier for the project"
    )
    status: ProjectStatus = Field(
        ProjectStatus.INACTIVE,
        title="Project Status",
        description="Current status of the project",
    )
    owner_uid: str = Field(..., title="Owner UID", description="Unique identifier for the project owner")


# This is a Pydantic model for the Project schema used for creating new projects - same as ProjectBase
class ProjectCreate(BaseModel):
    name: str = Field(..., title="Project Name", description="Name of the project")
    status: ProjectStatus = Field(
        ProjectStatus.INACTIVE,
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


# This is a Pydantic model for reading project data, which includes additional fields like id and created_at
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
