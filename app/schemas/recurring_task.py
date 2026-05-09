from datetime import datetime

from pydantic import BaseModel, Field

from app.models import RecurringFrequency


class RecurringTaskCreate(BaseModel):
    name: str = Field(..., title="Reccuring Template Name", description="Name of the reccuring template")
    description: str | None = Field(None, title="Description", description="Description of the reccuring template")
    project_id: int | None = Field(None, title="Project ID", description="ID of the project")
    frequency: RecurringFrequency = Field(..., title="Frequency", description="Frequency of the reccuring template")
    days: list[int] = Field(..., title="Days", description="Days of the week")
    timezone: str = Field(..., title="Timezone", description="Timezone of the reccuring template")
    task_id: int = Field(..., title="Task ID", description="ID of the task")

class RecurringTaskRead(RecurringTaskCreate):
    id: int = Field(..., title="ID", description="ID of the reccuring template")
    created_at: datetime = Field(..., title="Created At", description="Date and time when the reccuring template was created")
    next_run_at: datetime = Field(..., title="Next Run At", description="Date and time when the reccuring template will run next")
    last_run_at: datetime | None = Field(None, title="Last Run At", description="Date and time when the reccuring template was last run")
    is_active: bool = Field(..., title="Is Active", description="Whether the reccuring template is active")

class RecurringTaskUpdate(BaseModel):
    name: str | None = Field(None, title="Reccuring Template Name", description="Name of the reccuring template")
    description: str | None = Field(None, title="Description", description="Description of the reccuring template")
    project_id: int | None = Field(None, title="Project ID", description="ID of the project")
    frequency: RecurringFrequency | None = Field(None, title="Frequency", description="Frequency of the reccuring template")
    days: list[int] | None = Field(None, title="Days", description="Days of the week")
    timezone: str | None = Field(None, title="Timezone", description="Timezone of the reccuring template")
