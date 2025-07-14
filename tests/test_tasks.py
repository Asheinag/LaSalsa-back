import pytest
from httpx import AsyncClient


def create_task_function(client: AsyncClient):
    return client.post(
        "/tasks",
        json={"name": "Test Task", "description": "Created via test", "status": "TODO"},
    )


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    response = await create_task_function(client)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Task"


@pytest.mark.asyncio
async def test_get_task_by_id(client: AsyncClient):
    # First create a task to get
    response = await create_task_function(client)
    task_id = response.json()["id"]

    # Now get the task by ID
    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["name"] == "Test Task"


@pytest.mark.asyncio
async def test_get_tasks(client: AsyncClient):
    # First create a task to get
    await create_task_function(client)
    await create_task_function(client)
    await create_task_function(client)

    # Now get the tasks
    response = await client.get("/tasks")

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    # First create a task to delete
    response = await create_task_function(client)
    task_id = response.json()["id"]

    # Delete the task
    delete_response = await client.request(
        method="DELETE", url="/tasks", json={"id": task_id}
    )
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["id"] == task_id

    # Verify the task is deleted
    get_response = await client.get("/tasks/?offset=0&limit=100")
    assert get_response.status_code == 200
    tasks = get_response.json()
    assert all(task["id"] != task_id for task in tasks)


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    # First create a task to update
    response = await create_task_function(client)
    task_id = response.json()["id"]

    # Update the task
    update_response = await client.put(
        f"/tasks/{task_id}/update",
        json={
            "name": "Updated Task",
            "description": "Updated via test",
            "status": "IN_PROGRESS",
        },
    )
    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["name"] == "Updated Task"
    assert updated_task["status"] == "IN_PROGRESS"

    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["name"] == "Updated Task"
    assert data["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_update_task_status_done(client: AsyncClient):
    # First create a task to update
    response = await create_task_function(client)
    task_id = response.json()["id"]

    # Update the task status
    update_response = await client.patch(
        "/tasks/status", json={"id": task_id, "status": "DONE"}
    )
    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["status"] == "DONE"

    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["status"] == "DONE"
    assert (
        data["closed_at"] is not None
    )  # Assuming closed_at is set when status is DONE


@pytest.mark.asyncio
async def test_update_task_status_in_progress(client: AsyncClient):
    # First create a task to update
    response = await create_task_function(client)
    task_id = response.json()["id"]

    # Update the task status
    update_response = await client.patch(
        "/tasks/status", json={"id": task_id, "status": "IN_PROGRESS"}
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
