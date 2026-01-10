from datetime import datetime

import pytest
from httpx import AsyncClient

from app.celery_app import celery_app
from app.models.task import Task

build_task_chain = celery_app.tasks["app.tasks.build_task_chain"]


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, create_task_factory):
    """
    Проверка создания задачи через API
    """

    # Создаем задачу
    response = await create_task_factory()

    # Проверяем ответ
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Task"


@pytest.mark.asyncio
async def test_create_task_without_name(client: AsyncClient, create_task_factory):
    """
    Проверка создания задачи без имени через API
    """

    # Пытаемся создать задачу без имени
    response = await create_task_factory(
        {
            "description": "Task without a name",
            "status": "TODO",
        }
    )

    # Проверяем ответ
    assert response.status_code == 422  # Ожидаем ошибку валидации


@pytest.mark.asyncio
async def test_create_task_without_user_session(
    unauthenticated_client: AsyncClient,
):
    """
    Проверка создания задачи без активной сессии пользователя через API
    """

    # Пытаемся создать задачу без аутентификации
    response = await unauthenticated_client.post(
        "/tasks/",
        json={
            "name": "Task without User Session",
            "description": "Trying to create a task without user session",
            "status": "TODO",
        },
    )

    # Проверяем, что FastAPI вернул стандартную ошибку "Не аутентифицирован"
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_task_by_id(client: AsyncClient, create_task_factory):
    """
    Получение задачи по ID через API
    """

    # Создаем задачу
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Теперь получаем задачу по ID
    get_response = await client.get(f"/tasks/{task_id}")

    # Проверяем ответ
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["name"] == "Test Task"


@pytest.mark.asyncio
async def test_get_tasks(client: AsyncClient, create_task_factory):
    """
    Получение списка задач через API
    """

    # Сначала создаем несколько задач
    await create_task_factory()
    await create_task_factory()
    await create_task_factory()
    await create_task_factory()
    await create_task_factory()

    # Теперь получаем список задач с пагинацией
    response = await client.get("/tasks/?offset=0&limit=3")

    # Проверяем ответ с пагинацией
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3

    # Получаем следующий набор задач
    response_next = await client.get("/tasks/?offset=3&limit=3")

    # Проверяем ответ следующей страницы
    assert response_next.status_code == 200
    data_next = response_next.json()
    assert isinstance(data_next, list)
    assert len(data_next) == 2


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, create_task_factory):
    """
    Удаление задачи через API
    """

    # Сначала создаем задачу для удаления
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Удаляем задачу
    delete_response = await client.request(method="DELETE", url=f"/tasks/{task_id}")

    # Проверяем ответ
    assert delete_response.status_code == 204

    # Проверяем, что задача удалена
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

    # Сначала создаем задачу для обновления
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Обновляем задачу
    update_response = await client.put(
        f"/tasks/{task_id}",
        json={
            "name": "Updated Task",
            "description": "Updated via test",
            "status": "IN_PROGRESS",
        },
    )

    # Проверяем ответ
    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["name"] == "Updated Task"
    assert updated_task["status"] == "IN_PROGRESS"

    # Проверяем, что задача действительно обновлена
    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["name"] == "Updated Task"
    assert data["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_update_task_status_done(client: AsyncClient, create_task_factory):
    """
    Обновление статуса задачи в Done через API
    Проверяем именно Done чтобы убедиться, что closed_at устанавливается
    """

    # Сначала создаем задачу для обновления
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Обновляем статус задачи
    update_response = await client.patch(f"/tasks/{task_id}", json={"status": "DONE"})

    # Проверяем ответ
    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["status"] == "DONE"

    # Проверяем, что статус задачи действительно обновлен
    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["status"] == "DONE"

    # Проверяем, что время закрытия задачи установлено
    assert data["closed_at"] is not None

    # TODO можно добавить проверку, что closed_at близко к текущему времени


@pytest.mark.asyncio
async def test_update_task_status_in_progress(client: AsyncClient, create_task_factory):
    """
    Обновление статуса задачи в In Progress через API
    """

    # Сначала создаем задачу для обновления
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Обновляем статус задачи
    update_response = await client.patch(
        f"/tasks/{task_id}", json={"status": "IN_PROGRESS"}
    )

    # Проверяем ответ
    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["status"] == "IN_PROGRESS"

    # Проверяем, что статус задачи действительно обновлен
    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == task_id
    assert data["status"] == "IN_PROGRESS"

    # Проверяем, что время закрытия задачи сброшено
    assert data["closed_at"] is None


@pytest.mark.asyncio
async def test_update_task_wrong_status(client: AsyncClient, create_task_factory):
    """
    Обновление статуса задачи с неверным значением через API
    """
    # Сначала создаем задачу для обновления
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Пытаемся обновить статус задачи на неверное значение
    update_response = await client.patch(
        f"/tasks/{task_id}", json={"status": "WRONG_STATUS"}
    )

    # Проверяем ответ
    assert update_response.status_code == 422

    # Проверяем, что статус задачи не изменился
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

    # Сначала создаем задачу для обновления
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Меняем статус на DONE
    done_response = await client.patch(f"/tasks/{task_id}", json={"status": "DONE"})

    # Проверяем ответ и closed_at
    assert done_response.status_code == 200
    assert done_response.json()["closed_at"] is not None

    # Теперь меняем статус обратно на TODO
    reset_response = await client.patch(f"/tasks/{task_id}", json={"status": "TODO"})

    # Проверяем ответ и closed_at
    assert reset_response.status_code == 200
    data = reset_response.json()
    assert data["status"] == "TODO"
    assert data["closed_at"] is None


@pytest.mark.asyncio
async def test_get_task_children(client: AsyncClient, create_task_factory):
    """
    Получение цепочки задач через API
    """

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
    ]
    for task_data in tasks_data:
        await create_task_factory(task_data)

    # Получаем цепочку задач для родительской задачи
    response = await client.get("/tasks/1/children/")

    # Проверяем ответ
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["name"] == "Child Task 1"
    assert response_data[1]["name"] == "Child Task 2"


@pytest.mark.asyncio
async def test_create_task_chain(
    client: AsyncClient, db_session, monkeypatch, create_task_factory
):
    """
    Тест создания цепочки задач через Celery задачу
    """

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
        response = await create_task_factory(task_data)
        assert response.status_code == 201
        created_tasks.append(response.json())

    # Запускаем Celery задачу (она будет выполнена синхронно благодаря task_always_eager)
    monkeypatch.setattr("app.crud.chains.get_sync_session", lambda: db_session)
    result = build_task_chain.delay(created_tasks[0]["id"])
    chain = result.get(timeout=10)

    # Проверяем структуру цепочки
    assert chain["id"] == created_tasks[0]["id"]  # Используем реальный ID из ответа
    assert len(chain["children"]) == 2


def test_build_chain_with_direct_db(db_session, monkeypatch):
    """
    Тест создания цепочки задач через прямой доступ к БД
    """
    from app.crud import chains

    # 👇 monkeypatch локально
    monkeypatch.setattr(chains, "get_sync_session", lambda: db_session)

    # Создаем задачи напрямую в БД
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

    # Проверяем структуру цепочки
    assert chain["name"] == "Parent Task"
    assert len(chain["children"]) == 2
    assert any(c["name"] == "Child Task 1" for c in chain["children"])
    assert any(c["name"] == "Child Task 2" for c in chain["children"])


@pytest.mark.asyncio
async def test_get_task_by_id_not_found(client: AsyncClient):
    """
    Получение несуществующей задачи по ID через API
    """

    # Пытаемся получить задачу с несуществующим ID
    response = await client.get("/tasks/9999")

    # Проверяем ответ
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tasks_today(client: AsyncClient, create_task_factory):
    """
    Получение задач, запланированных на сегодня, через API
    """
    from datetime import datetime, timedelta

    # Определяем даты
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # Создаем задачи с разными датами planned_at
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

    # Получаем задачи, запланированные на сегодня
    response = await client.get("/tasks/today")

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Проверяем количество задач
    assert len(data) == 2
    task_names = [task["name"] for task in data]

    # Проверяем имена задач
    assert "Task Today 1" in task_names
    assert "Task Today 2" in task_names
    assert "Task Yesterday" not in task_names
    assert "Task Tomorrow" not in task_names


@pytest.mark.asyncio
async def test_get_tasks_later(client: AsyncClient, create_task_factory):
    """
    Получение задач, запланированных на позже, через API
    """

    from datetime import datetime, timedelta

    # Определяем даты
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    # Создаем задачи с разными датами planned_at
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

    # Получаем задачи, запланированные на позже
    response = await client.get("/tasks/later")

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Проверяем количество задач
    assert len(data) == 2
    task_names = [task["name"] for task in data]

    # Проверяем имена задач
    assert "Task Tomorrow" in task_names
    assert "Task Day After Tomorrow" in task_names


@pytest.mark.asyncio
async def test_task_create_with_invalid_project_id(
    client: AsyncClient, create_task_factory
):
    """
    Проверка создания задачи с несуществующим project_id через API
    """

    # Пытаемся создать задачу с несуществующим project_id
    response = await create_task_factory(
        {
            "name": "Task with Invalid Project",
            "description": "This task has an invalid project_id",
            "status": "TODO",
            "project_id": 9999,  # Предполагается, что такого проекта нет
        }
    )

    # Проверяем ответ
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_task_create_with_both_project_params(
    client: AsyncClient, create_task_factory
):
    """
    Проверка создания задачи с обоими параметрами project_id и project_name через API
    """

    # Пытаемся создать задачу с обоими параметрами project_id и project_name
    response = await create_task_factory(
        {
            "name": "Task with Both Project Params",
            "description": "This task has both project_id and project_name",
            "status": "TODO",
            "project_id": 1,
            "project_name": "Test Project",
        }
    )

    # Проверяем ответ
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_task_with_invalid_project_id(
    client: AsyncClient, create_task_factory
):
    """
    Проверка обновления задачи с несуществующим project_id через API
    """

    # Сначала создаем задачу для обновления
    response = await create_task_factory()
    task_id = response.json()["id"]

    # Пытаемся обновить задачу с несуществующим project_id
    update_response = await client.put(
        f"/tasks/{task_id}",
        json={
            "name": "Updated Task with Invalid Project",
            "description": "Trying to update with invalid project_id",
            "status": "IN_PROGRESS",
            "project_id": 9999,  # Предполагается, что такого проекта нет
        },
    )

    # Проверяем ответ
    assert update_response.status_code == 400


@pytest.mark.asyncio
async def test_get_tasks_without_user_session(unauthenticated_client: AsyncClient):
    """
    Проверка получения задач без активной сессии пользователя через API
    """

    # Пытаемся получить задачи без аутентификации
    response = await unauthenticated_client.get("/tasks/")

    # Проверяем, что FastAPI вернул стандартную ошибку "Не аутентифицирован"
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_another_user_task(
    client: AsyncClient,
    db_session,
):
    """
    Проверка получения задачи другого пользователя через API
    """

    # Создаем задачу от имени другого пользователя напрямую в БД
    from app.models.task import Task

    another_user_task = Task(
        name="Another User Task",
        description="Task owned by another user",
        status="TODO",
        created_at=datetime.now(),
        owner_uid="another_user_456",
    )
    db_session.add(another_user_task)
    db_session.commit()

    # Пытаемся получить эту задачу через API
    response = await client.get(f"/tasks/{another_user_task.id}")

    # Проверяем, что доступ запрещен
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_link_pomodoro_to_task(
    client: AsyncClient,
    create_task_factory,
    create_pomodoro_factory,
):
    """
    Проверка связывания сеанса Помодоро с задачей через API
    """

    # Сначала создаем задачу
    task_response = await create_task_factory()
    task_id = task_response.json()["id"]

    # Затем создаем сеанс Помодоро, связанный с этой задачей
    pomodoro_response = await create_pomodoro_factory(
        {
            "note": "Pomodoro linked to task",
            "duration_minutes": 25,
            "owner_uid": "test_user_123",
        }
    )
    assert pomodoro_response.status_code == 201
    pomodoro_data = pomodoro_response.json()

    # Добавляем связь между Помодоро и задачей
    pomodoro_id = pomodoro_data["id"]
    link_response = await client.patch(
        f"/tasks/{task_id}", json={"pomodoro_id": pomodoro_id}
    )
    assert link_response.status_code == 200

    # Проверяем, что задача теперь связана с сеансом Помодоро
    get_response = await client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    task_data = get_response.json()
    assert task_data["pomodoro_id"] == pomodoro_id
