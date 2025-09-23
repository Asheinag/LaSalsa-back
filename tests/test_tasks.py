from datetime import datetime

import pytest
from httpx import AsyncClient

from app.celery_app import celery_app
from app.models.task import Task

build_task_chain = celery_app.tasks["app.tasks.build_task_chain"]


def create_task_function(client: AsyncClient, task_data=None):
    if task_data is None:
        task_data = {
            "name": "Test Task",
            "description": "Created via test",
            "status": "TODO",
        }
    return client.post(
        "/tasks/",
        json=task_data,
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
    response = await client.get("/tasks/?offset=0&limit=100")

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
    delete_response = await client.request(method="DELETE", url=f"/tasks/{task_id}")
    assert delete_response.status_code == 204

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


@pytest.mark.asyncio
async def test_get_task_children(client: AsyncClient):
    tasks_data = [
        {
            "name": "Parent Task",
            "description": "Parent task description",
            "status": "TODO",
        },
        {
            "name": "Child Task 1",
            "description": "Child task 1 description",
            "status": "TODO",
            "parent_id": 1,
        },
        {
            "name": "Child Task 2",
            "description": "Child task 2 description",
            "status": "TODO",
            "parent_id": 1,
        },
    ]
    for task_data in tasks_data:
        await create_task_function(client, task_data)

    # Get the task chain for the parent task
    response = await client.get("/tasks/1/children/")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["name"] == "Child Task 1"
    assert response_data[1]["name"] == "Child Task 2"


@pytest.mark.asyncio
async def test_create_task_chain(client: AsyncClient, db_session, monkeypatch):
    # Создаем задачи через API
    tasks_data = [
        {
            "name": "Parent Task",
            "description": "Parent task description",
            "status": "TODO",
        },
        {
            "name": "Child Task 1",
            "description": "Child task 1 description",
            "status": "TODO",
            "parent_id": 1,
        },
        {
            "name": "Child Task 2",
            "description": "Child task 2 description",
            "status": "TODO",
            "parent_id": 1,
        },
        {
            "name": "Grandchild Task",
            "description": "Grandchild task description",
            "status": "TODO",
            "parent_id": 2,
        },
    ]
    created_tasks = []
    for task_data in tasks_data:
        response = await create_task_function(client, task_data)
        assert response.status_code == 201
        created_tasks.append(response.json())

    # Запускаем Celery задачу (она будет выполнена синхронно благодаря task_always_eager)
    monkeypatch.setattr("app.crud.chains.get_sync_session", lambda: db_session)
    result = build_task_chain.delay(created_tasks[0]["id"])
    chain = result.get(timeout=10)

    assert chain["id"] == created_tasks[0]["id"]  # Используем реальный ID из ответа
    assert len(chain["children"]) == 2


def test_build_chain_with_direct_db(db_session, monkeypatch):
    from app.crud import chains

    # 👇 monkeypatch локально
    monkeypatch.setattr(chains, "get_sync_session", lambda: db_session)

    # Дальше всё как раньше
    parent = Task(
        name="Parent Task",
        description="Parent",
        status="TODO",
        created_at=datetime.now(),
        owner_uid="test_user_123",
    )
    child1 = Task(
        name="Child Task 1",
        description="Child 1",
        status="TODO",
        created_at=datetime.now(),
        owner_uid="test_user_123",
        parent_id=1,
    )
    child2 = Task(
        name="Child Task 2",
        description="Child 2",
        status="TODO",
        created_at=datetime.now(),
        owner_uid="test_user_123",
        parent_id=1,
    )
    grandchild = Task(
        name="Grandchild Task",
        description="Grandchild",
        status="TODO",
        created_at=datetime.now(),
        owner_uid="test_user_123",
        parent_id=2,
    )

    db_session.add_all([parent, child1, child2, grandchild])
    db_session.commit()

    result = build_task_chain.apply((parent.id,), throw=True)
    chain = result.get()

    assert chain["name"] == "Parent Task"
    assert len(chain["children"]) == 2
    assert any(c["name"] == "Child Task 1" for c in chain["children"])
    assert any(c["name"] == "Child Task 2" for c in chain["children"])


@pytest.mark.asyncio
async def test_get_task_by_id_not_found(client: AsyncClient):
    response = await client.get("/tasks/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task_status_resets_closed_at(client: AsyncClient):
    response = await create_task_function(client)
    task_id = response.json()["id"]

    done_response = await client.patch(
        "/tasks/status", json={"id": task_id, "status": "DONE"}
    )
    assert done_response.status_code == 200
    assert done_response.json()["closed_at"] is not None

    reset_response = await client.patch(
        "/tasks/status", json={"id": task_id, "status": "TODO"}
    )
    assert reset_response.status_code == 200
    data = reset_response.json()
    assert data["status"] == "TODO"
    assert data["closed_at"] is None


@pytest.mark.asyncio
async def test_get_tasks_today(client: AsyncClient):
    # Create tasks with different planned_at dates
    from datetime import datetime, timedelta

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    tasks_data = [
        {
            "name": "Task Today 1",
            "description": "Task planned for today",
            "status": "TODO",
            "planned_at": today.isoformat(),
        },
        {
            "name": "Task Today 2",
            "description": "Another task planned for today",
            "status": "TODO",
            "planned_at": today.isoformat(),
        },
        {
            "name": "Task Yesterday",
            "description": "Task planned for yesterday",
            "status": "TODO",
            "planned_at": yesterday.isoformat(),
        },
        {
            "name": "Task Tomorrow",
            "description": "Task planned for tomorrow",
            "status": "TODO",
            "planned_at": tomorrow.isoformat(),
        },
    ]

    for task_data in tasks_data:
        await create_task_function(client, task_data)

    # Now get today's tasks
    response = await client.get("/tasks/today")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Only the two tasks planned for today
    task_names = [task["name"] for task in data]
    assert "Task Today 1" in task_names
    assert "Task Today 2" in task_names


@pytest.mark.asyncio
async def test_get_tasks_later(client: AsyncClient):
    # Create tasks with different planned_at dates
    from datetime import datetime, timedelta

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    tasks_data = [
        {
            "name": "Task Tomorrow",
            "description": "Task planned for tomorrow",
            "status": "TODO",
            "planned_at": tomorrow.isoformat(),
        },
        {
            "name": "Task Day After Tomorrow",
            "description": "Task planned for the day after tomorrow",
            "status": "TODO",
            "planned_at": day_after_tomorrow.isoformat(),
        },
        {
            "name": "Task Today",
            "description": "Task planned for today",
            "status": "TODO",
            "planned_at": today.isoformat(),
        },
    ]

    for task_data in tasks_data:
        await create_task_function(client, task_data)

    # Now get later tasks
    response = await client.get("/tasks/later")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Only the two tasks planned for later
    task_names = [task["name"] for task in data]
    assert "Task Tomorrow" in task_names
    assert "Task Day After Tomorrow" in task_names
