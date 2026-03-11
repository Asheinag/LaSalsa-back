"""
Роутер-тесты для AI Review.

LLM и Celery мокируются — реальных запросов нет.
"""

from unittest.mock import MagicMock, patch

import pytest

TEST_UID = "test_user_123"


# ---------------------------------------------------------------------------
# Фикстуры данных (только для этого файла)
# ---------------------------------------------------------------------------


@pytest.fixture
async def task(create_task_factory, create_review_factory):
    """
    Создаёт задачу через HTTP.
    create_review_factory указан (не используется) чтобы гарантировать,
    что db_session.drop_all/create_all отработает ДО создания задачи.
    """
    resp = await create_task_factory()
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def active_review(task, create_review_factory):
    return create_review_factory(task["id"])


@pytest.fixture
async def project(create_project_factory, create_project_review_factory):
    """
    Создаёт проект через HTTP.
    create_project_review_factory гарантирует, что db_session.drop_all/create_all
    отработает ДО создания проекта.
    """
    resp = await create_project_factory()
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def active_project_review(project, create_project_review_factory):
    return create_project_review_factory(project["id"])


# ---------------------------------------------------------------------------
# POST /ai-reviews/tasks/{task_id}/run
# ---------------------------------------------------------------------------


async def test_run_task_review_returns_celery_task_id(client, task):
    with patch(
        "app.crud.ai_review.run_task_review.delay",
        return_value=MagicMock(id="fake-celery-id"),
    ):
        response = await client.post(f"/ai-reviews/tasks/{task['id']}/run")

    assert response.status_code == 200
    assert response.json()["celery_task_id"] == "fake-celery-id"


async def test_run_task_review_unauthorized(unauthenticated_client):
    # Авторизация проверяется до обращения к БД, реальный task_id не нужен
    response = await unauthenticated_client.post("/ai-reviews/tasks/1/run")
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /ai-reviews/tasks/{task_id}/active
# ---------------------------------------------------------------------------


async def test_get_active_review_exists(client, active_review, task):
    response = await client.get(f"/ai-reviews/tasks/{task['id']}/active")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task["id"]
    assert "comment" in data


async def test_get_active_review_not_found(client, task):
    response = await client.get(f"/ai-reviews/tasks/{task['id']}/active")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /ai-reviews/tasks/{task_id}/history
# ---------------------------------------------------------------------------


async def test_get_task_review_history(client, task, create_review_factory):
    create_review_factory(task["id"], is_active=False)
    create_review_factory(task["id"], is_active=True)

    response = await client.get(f"/ai-reviews/tasks/{task['id']}/history")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /ai-reviews/status/{celery_task_id}
# ---------------------------------------------------------------------------


async def test_get_status_pending(client):
    with patch(
        "app.celery_app.AsyncResult",
        return_value=MagicMock(state="PENDING"),
    ):
        response = await client.get("/ai-reviews/status/fake-id")

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


async def test_get_status_done(client):
    with patch(
        "app.celery_app.AsyncResult",
        return_value=MagicMock(state="SUCCESS", result={}),
    ):
        response = await client.get("/ai-reviews/status/fake-id")

    assert response.status_code == 200
    assert response.json()["status"] == "done"


async def test_get_status_error(client):
    with patch(
        "app.celery_app.AsyncResult",
        return_value=MagicMock(state="FAILURE", result=Exception("fail")),
    ):
        response = await client.get("/ai-reviews/status/fake-id")

    assert response.status_code == 200
    assert response.json()["status"] == "error"


# ---------------------------------------------------------------------------
# GET /ai-reviews/{review_id}
# ---------------------------------------------------------------------------


async def test_get_review_by_id(client, active_review, task):
    response = await client.get(f"/ai-reviews/{active_review.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == active_review.id
    assert data["task_id"] == task["id"]
    assert "comment" in data


# ---------------------------------------------------------------------------
# POST /ai-reviews/projects/{project_id}/run
# ---------------------------------------------------------------------------


async def test_run_project_review_returns_celery_task_id(client, project):
    with patch(
        "app.crud.ai_review.run_project_review.delay",
        return_value=MagicMock(id="fake-project-celery-id"),
    ):
        response = await client.post(f"/ai-reviews/projects/{project['id']}/run")

    assert response.status_code == 200
    assert response.json()["celery_task_id"] == "fake-project-celery-id"


# ---------------------------------------------------------------------------
# GET /ai-reviews/projects/{project_id}/active
# ---------------------------------------------------------------------------


async def test_get_active_project_review_exists(client, active_project_review, project):
    response = await client.get(f"/ai-reviews/projects/{project['id']}/active")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project["id"]
    assert "comment" in data


async def test_get_active_project_review_not_found(client, project):
    response = await client.get(f"/ai-reviews/projects/{project['id']}/active")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /ai-reviews/projects/{project_id}/history
# ---------------------------------------------------------------------------


async def test_get_project_review_history(
    client, project, create_project_review_factory
):
    create_project_review_factory(project["id"], is_active=False)
    create_project_review_factory(project["id"], is_active=True)

    response = await client.get(f"/ai-reviews/projects/{project['id']}/history")
    assert response.status_code == 200
    assert len(response.json()) == 2
