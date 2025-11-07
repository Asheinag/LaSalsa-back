import pytest
from httpx import AsyncClient

from app.celery_app import celery_app

make_ai_tasks_review = celery_app.tasks["app.tasks.make_ai_tasks_review"]


@pytest.mark.asyncio
async def test_ai_review_tasks(
    client: AsyncClient, db_session, monkeypatch, create_task_factory
):
    """
    Тестирование эндпоинта обзора задач с помощью ИИ.
    """
    # Создаем тестовые задачи
    tasks_data = [
        {
            "name": "Task 1",
            "description": "First task description",
            "status": "TODO",
        },
        {
            "name": "Task 2",
            "description": "Second task description",
            "status": "TODO",
        },
        {
            "name": "Task 3",
            "description": "Third task description",
            "status": "TODO",
        },
    ]
    created_tasks = []
    for task_data in tasks_data:
        response = await create_task_factory(task_data)
        assert response.status_code == 201
        created_tasks.append(response.json())

    # Запускаем Celery задачу для создания ревью
    monkeypatch.setattr("app.crud.task_ai_comment.get_sync_session", lambda: db_session)
    result = make_ai_tasks_review.delay("test_user_123")
    res = result.get(timeout=10)

    # Проверяем результат выполнения
    assert res["status"] == "done"
    assert res["ai_comments_created"] == 3


@pytest.mark.asyncio
async def test_get_review_by_task(
    client: AsyncClient, db_session, monkeypatch, create_task_factory
):
    """
    Тестирование эндпоинта получения комментария
    """
    # Создаем задачу
    response = await create_task_factory()
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Создаем ревью для задачи
    monkeypatch.setattr("app.crud.task_ai_comment.get_sync_session", lambda: db_session)
    result = make_ai_tasks_review.delay("test_user_123")
    res = result.get(timeout=10)
    assert res["status"] == "done"

    # Получаем ревью по задаче
    get_response = await client.get(f"/ai/review/{task_id}")
    assert get_response.status_code == 200
    review_data = get_response.json()

    # Проверяем заполнение задачи
    assert review_data["comment"] == "AI review comment for task Test Task"
    assert review_data["task_id"] == 1
    assert review_data["is_active"] is True


@pytest.mark.asyncio
async def test_new_review_deactivate_previous(
    client: AsyncClient, db_session, monkeypatch, create_task_factory
):
    """
    Проверяем что при создании новых ревью старые отмечаются неактивными
    """

    # Создаем тестовые задачи
    tasks_data = [
        {
            "name": "Task 1",
            "description": "First task description",
            "status": "TODO",
        },
        {
            "name": "Task 2",
            "description": "Second task description",
            "status": "TODO",
        },
        {
            "name": "Task 3",
            "description": "Third task description",
            "status": "TODO",
        },
    ]
    created_tasks = []
    for task_data in tasks_data:
        response = await create_task_factory(task_data)
        assert response.status_code == 201
        created_tasks.append(response.json())

    # Запускаем Celery задачу для создания ревью
    monkeypatch.setattr("app.crud.task_ai_comment.get_sync_session", lambda: db_session)
    result = make_ai_tasks_review.delay("test_user_123")
    res = result.get(timeout=10)
    assert res["status"] == "done"

    # Запускаем еще раз
    monkeypatch.setattr("app.crud.task_ai_comment.get_sync_session", lambda: db_session)
    result = make_ai_tasks_review.delay("test_user_123")
    res = result.get(timeout=10)

    # Получаем все записи по первой задаче
    first_task_id = created_tasks[0]["id"]
    get_response = await client.get(f"/ai/review/{first_task_id}/all")
    response_data = get_response.json()


    # Проверяем результат
    assert len(response_data) > 1
    assert response_data[0]["task_id"] == 1
    assert response_data[1]["task_id"] == 1
    assert response_data[0]["comment"] == "AI review comment for task Task 1"
    assert response_data[1]["comment"] == "AI review comment for task Task 1"
    assert response_data[0]["is_active"] is False
    assert response_data[1]["is_active"] is True
