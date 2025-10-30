from datetime import datetime

from pydantic import BaseModel, Field


# Это модель Pydantic для схем TaskAIComment
class TaskAICommentBase(BaseModel):
    comment: str = Field(..., title="Comment", description="AI-generated comment for the task")


class TaskAIComment(TaskAICommentBase):
    id: int = Field(..., title="ID", description="Unique identifier for the AI comment")
    created_at: datetime = Field(..., title="Created At", description="Timestamp when the comment was created")
    task_id: int = Field(..., title="Task ID", description="Identifier of the associated task")
    is_active: bool = Field(..., title="Is Active", description="Indicates if the comment is active")
