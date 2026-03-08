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
    task_id: int = Field(
        ..., title="Task ID", description="Identifier of the associated task"
    )
    comment: dict = Field(
        ..., title="AI Comment", description="Comment created by AI for task"
    )

    @field_validator("comment", mode="before")
    @classmethod
    def parse_comment(cls, v: str | dict) -> dict:
        if isinstance(v, str):
            return json.loads(v)
        return v
