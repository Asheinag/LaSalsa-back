import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# Это модель Pydantic для схем TaskAIComment
class AIReviewShort(BaseModel):
    id: int = Field(..., title="ID", description="Unique identifier for the AI comment")
    is_active: bool = Field(
        ..., title="Is Active", description="Indicates if the comment is active"
    )


class AIReviewRead(AIReviewShort):
    created_at: datetime = Field(
        ..., title="Created At", description="Timestamp when the comment was created"
    )
    task_id: int | None = Field(
        default=None, title="Task ID", description="Identifier of the associated task"
    )
    project_id: int | None = Field(
        default=None, title="Project ID", description="Identifier of the associated project"
    )
    comment: dict = Field(
        ..., title="AI Comment", description="Comment created by AI"
    )

    @field_validator("comment", mode="before")
    @classmethod
    def parse_comment(cls, v: str | dict) -> dict:
        if isinstance(v, str):
            return json.loads(v)
        return v
