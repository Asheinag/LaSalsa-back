"""
Тесты переходов статусов задачи: DONE / IN_PROGRESS / TODO, логика closed_at.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_task_status_done(client: AsyncClient, create_task_factory):
    """
    Обновление статуса задачи в Done через API
    Проверяем именно Done чтобы убедиться, что closed_at устанавливается
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    update_response = await client.patch(f"/tasks/{task_id}", json={"status": "DONE"})

    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["status"] == "DONE"

    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["status"] == "DONE"
    assert data["closed_at"] is not None


@pytest.mark.asyncio
async def test_update_task_status_in_progress(client: AsyncClient, create_task_factory):
    """
    Обновление статуса задачи в In Progress через API
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    update_response = await client.patch(
        f"/tasks/{task_id}", json={"status": "IN_PROGRESS"}
    )

    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["status"] == "IN_PROGRESS"

    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["status"] == "IN_PROGRESS"
    assert data["closed_at"] is None


@pytest.mark.asyncio
async def test_update_task_wrong_status(client: AsyncClient, create_task_factory):
    """
    Обновление статуса задачи с неверным значением через API
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    update_response = await client.patch(
        f"/tasks/{task_id}", json={"status": "WRONG_STATUS"}
    )

    assert update_response.status_code == 422

    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["status"] == "TODO"


@pytest.mark.asyncio
async def test_update_task_status_resets_closed_at(
    client: AsyncClient, create_task_factory
):
    """
    Обновление статуса задачи из DONE в TODO сбрасывает closed_at
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    done_response = await client.patch(f"/tasks/{task_id}", json={"status": "DONE"})

    assert done_response.status_code == 200
    assert done_response.json()["closed_at"] is not None

    reset_response = await client.patch(f"/tasks/{task_id}", json={"status": "TODO"})

    assert reset_response.status_code == 200
    data = reset_response.json()
    assert data["status"] == "TODO"
    assert data["closed_at"] is None
