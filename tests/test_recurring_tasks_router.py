import pytest
from httpx import AsyncClient

from app.models import RecurringFrequency

REC_ROUTE = "/recurring-tasks"


@pytest.mark.asyncio
async def test_create_rec_task(
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


@pytest.mark.asyncio
async def test_get_rec_tasks(
    client: AsyncClient, create_task_factory, create_recurring_task_factory
):
    task1 = {
        "name": "Test Task 1",
        "description": "Created via test",
    }
    task2 = {
        "name": "Test Task 2",
        "description": "Created via test",
    }
    await create_task_factory(task1)
    await create_task_factory(task2)
    recurring_task_data1 = {
        "name": "Test Recurring Task by Test",
        "description": "Created via test",
        "frequency": RecurringFrequency.DAILY,
        "days": [],
        "timezone": "UTC",
        "task_id": 1,
    }
    recurring_task_data2 = {
        "name": "Test Recurring Task 2 by Test",
        "description": "Created via test",
        "frequency": RecurringFrequency.DAILY,
        "days": [],
        "timezone": "UTC",
        "task_id": 2,
    }
    await create_recurring_task_factory(recurring_task_data1)
    await create_recurring_task_factory(recurring_task_data2)
    response = await client.get("/recurring-tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_rec_task(
    client: AsyncClient, create_task_factory, create_recurring_task_factory
):
    task1 = {
        "name": "Test Task 1",
        "description": "Created via test",
    }
    task2 = {
        "name": "Test Task 2",
        "description": "Created via test",
    }
    await create_task_factory(task1)

    await create_task_factory(task2)

    recurring_task_data1 = {
        "name": "Test Recurring Task by Test",
        "description": "Created via test",
        "frequency": RecurringFrequency.DAILY,
        "days": [],
        "timezone": "UTC",
        "task_id": 1,
    }
    recurring_task_data2 = {
        "name": "Test Recurring Task 2 by Test",
        "description": "Created via test",
        "frequency": RecurringFrequency.DAILY,
        "days": [],
        "timezone": "UTC",
        "task_id": 2,
    }
    await create_recurring_task_factory(recurring_task_data1)
    await create_recurring_task_factory(recurring_task_data2)

    response = await client.get(f"{REC_ROUTE}/1")
    print(response)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Recurring Task by Test"
    assert data["description"] == "Created via test"


@pytest.mark.asyncio
async def test_get_rec_task_not_found(client: AsyncClient):
    response = await client.get(f"{REC_ROUTE}/1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_rec_task(
    client: AsyncClient, create_recurring_task_factory, create_task_factory
):
    task_data = {
        "name": "Test Task",
        "description": "Created via test",
    }
    await create_task_factory(task_data)
    recurring_task_data = {
        "name": "Test Recurring Task by Test",
        "description": "Created via test",
        "frequency": RecurringFrequency.DAILY,
        "days": [],
        "timezone": "UTC",
    }
    response = await create_recurring_task_factory(recurring_task_data)

    data = response.json()
    assert data["name"] == "Test Recurring Task by Test"
    assert data["description"] == "Created via test"
    assert data["frequency"] == "daily"
    assert data["days"] == []
    assert data["timezone"] == "UTC"

    await client.patch(f"{REC_ROUTE}/1", json={"name": "Test Recurring Task by Test 2"})
    response = await client.get(f"{REC_ROUTE}/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Recurring Task by Test 2"
    assert data["description"] == "Created via test"
    assert data["frequency"] == "daily"
    assert data["days"] == []
    assert data["timezone"] == "UTC"


@pytest.mark.asyncio
async def test_delete_rec_task(
    client: AsyncClient, create_recurring_task_factory, create_task_factory
):
    await create_task_factory()

    response = await create_recurring_task_factory()
    data = response.json()
    print(data)

    assert data["name"] == "Test Recurring Task"
    await client.delete(f"{REC_ROUTE}/1")

    response = await client.get(f"{REC_ROUTE}/1")
    assert response.status_code == 404
