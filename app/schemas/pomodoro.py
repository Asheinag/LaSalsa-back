from pydantic import BaseModel, Field


# Схема Помодоро для создания нового сеанса работы
class PomodoroCreate(BaseModel):
    note: str | None = Field(
        None, title="Note", description="Optional note for the Pomodoro session"
    )
    duration_minutes: int = Field(
        25,
        title="Duration Minutes",
        description="Duration of the Pomodoro session in minutes",
    )
    previous_pomodoro_id: int | None = Field(
        None,
        title="Previous Pomodoro ID",
        description="ID of the previous Pomodoro session",
    )


# Схема Помодоро для чтения сеанса работы
class PomodoroRead(BaseModel):
    id: int = Field(
        ..., title="ID", description="Unique identifier for the Pomodoro session"
    )
    note: str | None = Field(
        None, title="Note", description="Optional note for the Pomodoro session"
    )
    duration_minutes: int = Field(
        ...,
        title="Duration Minutes",
        description="Duration of the Pomodoro session in minutes",
    )
    owner_uid: str = Field(
        ..., title="Owner UID", description="Unique identifier for the Pomodoro owner"
    )
    previous_pomodoro_id: int | None = Field(
        None,
        title="Previous Pomodoro ID",
        description="ID of the previous Pomodoro session",
    )


class PomodoroUpdate(BaseModel):
    note: str | None = Field(
        None, title="Note", description="Updated note for the Pomodoro session"
    )
    duration_minutes: int | None = Field(
        None,
        title="Duration Minutes",
        description="Updated duration of the Pomodoro session in minutes",
    )
