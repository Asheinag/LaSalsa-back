"""
Роутер-тесты для Tasks: CRUD, авторизация, валидация, иерархия, фильтры.
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.task import Task


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, create_task_factory):
    """
    Проверка создания задачи через API
    """
    response = await create_task_factory()

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Task"


@pytest.mark.asyncio
async def test_create_task_without_name(client: AsyncClient, create_task_factory):
    """
    Проверка создания задачи без имени через API
    """
    response = await create_task_factory(
        {
            "description": "Task without a name",
            "status": "TODO",
        }
    )

    assert response.status_code == 422  # Ожидаем ошибку валидации


@pytest.mark.asyncio
async def test_create_task_without_user_session(
    unauthenticated_client: AsyncClient,
):
    """
    Проверка создания задачи без активной сессии пользователя через API
    """
    response = await unauthenticated_client.post(
        "/tasks/",
        json={
            "name": "Task without User Session",
            "description": "Trying to create a task without user session",
            "status": "TODO",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_task_by_id(client: AsyncClient, create_task_factory):
    """
    Получение задачи по ID через API
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    get_response = await client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["name"] == "Test Task"


@pytest.mark.asyncio
async def test_get_task_by_id_not_found(client: AsyncClient):
    """
    Получение несуществующей задачи по ID через API
    """
    response = await client.get("/tasks/9999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tasks(client: AsyncClient, create_task_factory):
    """
    Получение списка задач через API
    """
    await create_task_factory()
    await create_task_factory()
    await create_task_factory()
    await create_task_factory()
    await create_task_factory()

    response = await client.get("/tasks/?offset=0&limit=3")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3

    response_next = await client.get("/tasks/?offset=3&limit=3")

    assert response_next.status_code == 200
    data_next = response_next.json()
    assert isinstance(data_next, list)
    assert len(data_next) == 2


@pytest.mark.asyncio
async def test_get_tasks_without_user_session(unauthenticated_client: AsyncClient):
    """
    Проверка получения задач без активной сессии пользователя через API
    """
    response = await unauthenticated_client.get("/tasks/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_another_user_task(
    client: AsyncClient,
    db_session,
):
    """
    Проверка получения задачи другого пользователя через API
    """
    another_user_task = Task(
        name="Another User Task",
        description="Task owned by another user",
        status="TODO",
        created_at=datetime.now(),
        owner_uid="another_user_456",
    )
    db_session.add(another_user_task)
    db_session.commit()

    response = await client.get(f"/tasks/{another_user_task.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, create_task_factory):
    """
    Удаление задачи через API
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    delete_response = await client.request(method="DELETE", url=f"/tasks/{task_id}")

    assert delete_response.status_code == 204

    deleted_response = await client.get(f"/tasks/{task_id}")
    assert deleted_response.status_code == 404
    get_response = await client.get("/tasks/?offset=0&limit=100")
    assert get_response.status_code == 200
    tasks = get_response.json()
    assert all(task["id"] != task_id for task in tasks)


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, create_task_factory):
    """
    Обновление задачи через API
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    update_response = await client.put(
        f"/tasks/{task_id}",
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
async def test_task_create_with_invalid_project_id(
    client: AsyncClient, create_task_factory
):
    """
    Проверка создания задачи с несуществующим project_id через API
    """
    response = await create_task_factory(
        {
            "name": "Task with Invalid Project",
            "description": "This task has an invalid project_id",
            "status": "TODO",
            "project_id": 9999,
        }
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_task_create_with_both_project_params(
    client: AsyncClient, create_task_factory
):
    """
    Проверка создания задачи с обоими параметрами project_id и project_name через API
    """
    response = await create_task_factory(
        {
            "name": "Task with Both Project Params",
            "description": "This task has both project_id and project_name",
            "status": "TODO",
            "project_id": 1,
            "project_name": "Test Project",
        }
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_task_with_invalid_project_id(
    client: AsyncClient, create_task_factory
):
    """
    Проверка обновления задачи с несуществующим project_id через API
    """
    response = await create_task_factory()
    task_id = response.json()["id"]

    update_response = await client.put(
        f"/tasks/{task_id}",
        json={
            "name": "Updated Task with Invalid Project",
            "description": "Trying to update with invalid project_id",
            "status": "IN_PROGRESS",
            "project_id": 9999,
        },
    )

    assert update_response.status_code == 400


@pytest.mark.asyncio
async def test_get_task_children(client: AsyncClient, create_task_factory):
    """
    Получение цепочки задач через API
    """
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
        await create_task_factory(task_data)

    response = await client.get("/tasks/1/children/")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["name"] == "Child Task 1"
    assert response_data[1]["name"] == "Child Task 2"


@pytest.mark.asyncio
async def test_get_tasks_today(client: AsyncClient, create_task_factory):
    """
    Получение задач, запланированных на сегодня, через API
    """
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
        await create_task_factory(task_data)

    response = await client.get("/tasks/today")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    task_names = [task["name"] for task in data]
    assert "Task Today 1" in task_names
    assert "Task Today 2" in task_names
    assert "Task Yesterday" not in task_names
    assert "Task Tomorrow" not in task_names


@pytest.mark.asyncio
async def test_get_tasks_later(client: AsyncClient, create_task_factory):
    """
    Получение задач, запланированных на позже, через API
    """
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
        await create_task_factory(task_data)

    response = await client.get("/tasks/later")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    task_names = [task["name"] for task in data]
    assert "Task Tomorrow" in task_names
    assert "Task Day After Tomorrow" in task_names


@pytest.mark.asyncio
async def test_link_pomodoro_to_task(
    client: AsyncClient,
    create_task_factory,
    create_pomodoro_factory,
):
    """
    Проверка связывания сеанса Помодоро с задачей через API
    """
    task_response = await create_task_factory()
    task_id = task_response.json()["id"]

    pomodoro_response = await create_pomodoro_factory(
        {
            "note": "Pomodoro linked to task",
            "duration_minutes": 25,
            "owner_uid": "test_user_123",
        }
    )
    assert pomodoro_response.status_code == 201
    pomodoro_data = pomodoro_response.json()

    pomodoro_id = pomodoro_data["id"]
    link_response = await client.patch(
        f"/tasks/{task_id}", json={"pomodoro_id": pomodoro_id}
    )
    assert link_response.status_code == 200

    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    task_data = get_response.json()
    assert task_data["pomodoro_id"] == pomodoro_id
