import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, create_project_factory):
    """
    Проверка создания проекта через API.
    """
    # Создаем проект
    response = await create_project_factory()

    # Проверяем ответ
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "INACTIVE"
    assert data["owner_uid"] == "test_user_123"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_projects(client: AsyncClient, create_project_factory):
    """
    Проверка получения списка проектов через API.
    """
    # Создаем проект
    await create_project_factory()

    # Получаем список проектов
    response = await client.get("/projects/")

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "name" in data[0]
    assert "status" in data[0]
    assert "owner_uid" in data[0]
    assert "color_id" in data[0]


@pytest.mark.asyncio
async def test_get_projects_empty(client: AsyncClient):
    """
    Проверка получения списка проектов, когда их нет.
    """
    response = await client.get("/projects/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient, create_project_factory):
    """
    Проверка получения проекта по ID через API.
    """
    # Создаем проект
    response = await create_project_factory()
    data = response.json()
    project_id = data["id"]

    # Получаем проект по ID
    full_response = await client.get(f"/projects/{project_id}")

    # Проверяем ответ
    assert full_response.status_code == 200
    project_data = full_response.json()
    assert project_data["id"] == project_id
    assert project_data["name"] == "Test Project"
    assert "created_at" in project_data


@pytest.mark.asyncio
async def test_create_project_with_all_fields(client: AsyncClient):
    """
    Проверка создания проекта через API с заполнением всех полей.
    """

    # Создаем проект
    response = await client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "Created via test",
            "type": "LIST",
            "status": "INACTIVE",
            "deadline": "2023-12-31T23:59:59z",
            "color_id": 2,
        },
    )
    data = response.json()

    # Проверяем ответ
    assert data["name"] == "Test Project"
    assert data["status"] == "INACTIVE"
    assert "id" in data

    # Получаем полный проект по ID
    full_response = await client.get(f"/projects/{data['id']}")
    full_data = full_response.json()

    # Проверяем все поля
    assert full_data["name"] == "Test Project"
    assert full_data["description"] == "Created via test"
    assert full_data["type"] == "LIST"
    assert full_data["status"] == "INACTIVE"
    assert full_data["deadline"] == "2023-12-31T23:59:59Z"
    assert full_data["owner_uid"] == "test_user_123"
    assert full_data["color_id"] == 2


@pytest.mark.asyncio
async def test_unsuccessful_create_project_with_invalid_status(client: AsyncClient):
    """
    Проверка неуспешного создания проекта с неправильным значением статуса
    """
    response = await client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "Created via test",
            "type": "LIST",
            "status": "INVALID_STATUS",  # Неверное значение статуса
        },
    )

    # Проверка ответа
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unsuccessful_create_project_with_invalid_type(client: AsyncClient):
    """
    Проверка неуспешного создания проекта с неправильным значением типа
    """
    response = await client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "Created via test",
            "type": "INVALID_TYPE",  # Неверное значение типа
            "status": "INACTIVE",
        },
    )

    # Проверка ответа
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_tasks_by_project(
    client: AsyncClient, create_project_factory, create_task_factory
):
    """
    Проверка получения  списка задач по проекту через API.
    """

    # Создаем проект и задачи
    project_response = await create_project_factory({"name": "Project with Tasks"})

    project_id = project_response.json()["id"]

    await create_task_factory(
        {
            "name": "Task 1",
            "description": "Task 1 description",
            "status": "TODO",
            "project_id": project_id,
        },
    )
    await create_task_factory(
        {
            "name": "Task 2",
            "description": "Task 2 description",
            "status": "TODO",
            "project_id": project_id,
        },
    )
    await create_task_factory(
        {"name": "Task 32", "description": "Task 32 description", "status": "TODO"},
    )

    # Получаем задачи по проекту
    response = await client.get(f"/projects/{project_id}/tasks")

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(task["project_id"] == project_id for task in data)


@pytest.mark.asyncio
async def test_get_tasks_by_project_empty(client: AsyncClient, create_project_factory):
    """
    Проверка получения задач по пустому проекту.
    """

    # Создаем пустой проект
    project_response = await create_project_factory({"name": "Empty Project"})
    project_id = project_response.json()["id"]

    # Получаем задачи по проекту
    response = await client.get(f"/projects/{project_id}/tasks")

    # Проверяем ответ
    assert response.status_code == 200
    assert response.json() == []
