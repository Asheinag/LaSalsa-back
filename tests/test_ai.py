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

    # Запускаем Celery задачу (она будет выполнена синхронно благодаря task_always_eager)
    monkeypatch.setattr("app.crud.task_ai_comment.get_sync_session", lambda: db_session)
    print("Starting AI review task...")
    result = make_ai_tasks_review.delay("test_user_123")
    print("Waiting for result...")
    res = result.get(timeout=10)

    assert res["status"] == "done"
    assert res["ai_comments_created"] > 0
