from datetime import datetime

from pydantic import BaseModel, Field


# Это модель Pydantic для схем TaskAIComment
class TaskAIReviewShort(BaseModel):
    id: int = Field(..., title="ID", description="Unique identifier for the AI comment")
    is_active: bool = Field(
        ..., title="Is Active", description="Indicates if the comment is active"
    )

class TaskAIReviewRead(TaskAIReviewShort):
    created_at: datetime = Field(
        ..., title="Created At", description="Timestamp when the comment was created"
    )
    task_id: int = Field(
        ..., title="Task ID", description="Identifier of the associated task"
    )
    comment: str = Field(
        ..., title="AI Comment", description="Comment created by AI for task"
    )

# Это модель Pydantic для схем ProjectAIComment
class ProjectAIReviewShort(BaseModel):
    id: int = Field(..., title="ID", description="Unique identifier for the AI comment")
    is_active: bool = Field(
        ..., title="Is Active", description="Indicates if the comment is active"
    )

class ProjectAIReviewRead(ProjectAIReviewShort):
    created_at: datetime = Field(
        ..., title="Created At", description="Timestamp when the comment was created"
    )
    task_id: int = Field(
        ..., title="Task ID", description="Identifier of the associated task"
    )
    comment: str = Field(
        ..., title="AI Comment", description="Comment created by AI for task"
    )
