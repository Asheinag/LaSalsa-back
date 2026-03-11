"""
Тесты Celery-таска build_task_chain: построение иерархии задач.
"""

from datetime import datetime

import pytest
from httpx import AsyncClient

from app.celery_app import celery_app
from app.models.task import Task

build_task_chain = celery_app.tasks["app.tasks.build_task_chain"]


@pytest.mark.asyncio
async def test_create_task_chain(
    client: AsyncClient, db_session, monkeypatch, create_task_factory
):
    """
    Тест создания цепочки задач через Celery задачу
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

    monkeypatch.setattr("app.crud.chains.get_sync_session", lambda: db_session)
    result = build_task_chain.delay(created_tasks[0]["id"])
    chain = result.get(timeout=10)

    assert chain["id"] == created_tasks[0]["id"]
    assert len(chain["children"]) == 2


def test_build_chain_with_direct_db(db_session, monkeypatch):
    """
    Тест создания цепочки задач через прямой доступ к БД
    """
    from app.crud import chains

    monkeypatch.setattr(chains, "get_sync_session", lambda: db_session)

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
