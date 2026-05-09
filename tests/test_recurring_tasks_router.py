import pytest
from httpx import AsyncClient

from app.models import RecurringFrequency


@pytest.mark.asyncio
async def test_create_task(
    client: AsyncClient, create_task_factory, create_recurring_task_factory
):
    await create_task_factory()
    recurring_task_data = {
        "name": "Test Recurring Task by Test",
        "description": "Created via test",
        "frequency": RecurringFrequency.DAILY,
        "days": [],
        "timezone": "UTC",
        "task_id": 1,
    }
    response = await create_recurring_task_factory(recurring_task_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Recurring Task by Test"
    assert data["description"] == "Created via test"
    assert data["frequency"] == "daily"
    assert data["next_run_at"] is not None
    assert data["last_run_at"] is None
    assert data["is_active"] is True
