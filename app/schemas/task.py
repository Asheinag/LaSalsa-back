from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.common import TaskStatus

# This is a Pydantic model for the Task schema
class TaskBase(BaseModel):
    name: str = Field(..., title="Task Name", description="Name of the task")
    description: str = Field(..., title="Task Description", description="Description of the task")
    planned_at: Optional[datetime] = Field(None, title="Planned At", description="Planned date and time for the task")
    closed_at: Optional[datetime] = Field(None, title="Closed At", description="Closed date and time for the task")
    status: TaskStatus = Field(TaskStatus.TODO, title="Task Status", description="Current status of the task")
    project_id: Optional[int] = Field(None, title="Project ID", description="ID of the project associated with the task")
    project_name: Optional[str] = Field(None, title="Project Name", description="Name of the project associated with the task")
    parent_id: Optional[int] = Field(None, title="Parent Task ID", description="ID of the parent task if this is a subtask")
    model_config = ConfigDict(from_attributes=True)

# This is a Pydantic model for the Task schema used for creating new tasks - same as TaskBase
class TaskCreate(TaskBase):
    class Config:
        use_enum_values = True

class TaskShort(BaseModel):
    id: int = Field(..., title="Task ID", description="Unique identifier for the task")
    name: str = Field(..., title="Task Name", description="Name of the task")
    status: TaskStatus = Field(..., title="Task Status", description="Current status of the task")
    planned_at: Optional[datetime] = Field(None, title="Planned At", description="Planned date and time for the task")
    closed_at: Optional[datetime] = Field(None, title="Closed At", description="Closed date and time for the task")
    project_id: Optional[int] = Field(None, title="Project ID", description="ID of the project associated with the task")

    model_config = ConfigDict(from_attributes=True)

class TaskRead(TaskBase):
    id: int = Field(..., title="Task ID", description="Unique identifier for the task")
    created_at: datetime = Field(..., title="Created At", description="Creation date and time of the task")

    model_config = ConfigDict(from_attributes=True)


class TaskStatusUpdate(BaseModel):
    id: int = Field(..., title="Status ID", description="Unique identifier for the task status")
    status: TaskStatus = Field(..., title="Task Status", description="Current status of the task")

    model_config = ConfigDict(from_attributes=True)        

class TaskID(BaseModel):
    id: int = Field(..., title="Task ID", description="Unique identifier for the task")

    model_config = ConfigDict(from_attributes=True)