"""
CRUD-тесты для AI Review.

Используем async_db для тестирования асинхронных CRUD-функций,
db_session — для синхронных вспомогательных функций.
"""

import json
from datetime import datetime

import pytest

from app.crud.ai_review import (
    _deactivate_active_reviews,
    get_all_comments,
    get_last_active_review,
    get_review_by_id,
)
from app.models import AIReview, Project, Task

TEST_UID = "test_user_123"
OTHER_UID = "other_user_uid"


# ---------------------------------------------------------------------------
# Фикстуры данных (только для этого файла)
# ---------------------------------------------------------------------------


@pytest.fixture
async def task(async_db):
    t = Task(
        name="Test Task",
        owner_uid=TEST_UID,
        status="TODO",
        created_at=datetime.utcnow(),
    )
    async_db.add(t)
    await async_db.commit()
    await async_db.refresh(t)
    return t


@pytest.fixture
async def project(async_db):
    p = Project(
        name="Test Project",
        owner_uid=TEST_UID,
        status="ACTIVE",
        type="PROJECT",
        created_at=datetime.utcnow(),
    )
    async_db.add(p)
    await async_db.commit()
    await async_db.refresh(p)
    return p


@pytest.fixture
async def active_review(async_db, task):
    r = AIReview(
        task_id=task.id,
        owner_uid=TEST_UID,
        is_active=True,
        comment=json.dumps({"verdict": "Test verdict", "score": 7, "questions": []}),
    )
    async_db.add(r)
    await async_db.commit()
    await async_db.refresh(r)
    return r


# ---------------------------------------------------------------------------
# get_last_active_review
# ---------------------------------------------------------------------------


async def test_get_active_review_returns_active(async_db, active_review, task):
    result = await get_last_active_review(async_db, TEST_UID, task_id=task.id)
    assert result is not None
    assert result.id == active_review.id


async def test_get_active_review_returns_none_when_empty(async_db, task):
    result = await get_last_active_review(async_db, TEST_UID, task_id=task.id)
    assert result is None


async def test_get_active_review_returns_none_for_wrong_user(
    async_db, active_review, task
):
    result = await get_last_active_review(async_db, OTHER_UID, task_id=task.id)
    assert result is None


# ---------------------------------------------------------------------------
# _deactivate_active_reviews (синхронная функция — используем db_session)
# ---------------------------------------------------------------------------


def test_deactivate_sets_is_active_false(db_session):
    task = Task(
        name="T",
        owner_uid=TEST_UID,
        status="TODO",
        created_at=datetime.utcnow(),
    )
    db_session.add(task)
    db_session.commit()

    review = AIReview(
        task_id=task.id,
        owner_uid=TEST_UID,
        is_active=True,
        comment=json.dumps({"verdict": "x", "score": 5, "questions": []}),
    )
    db_session.add(review)
    db_session.commit()

    _deactivate_active_reviews(db_session, TEST_UID, task_id=task.id)
    db_session.commit()

    db_session.refresh(review)
    assert review.is_active is False


def test_deactivate_does_not_affect_other_tasks(db_session):
    task = Task(
        name="T",
        owner_uid=TEST_UID,
        status="TODO",
        created_at=datetime.utcnow(),
    )
    project = Project(
        name="P",
        owner_uid=TEST_UID,
        status="ACTIVE",
        type="PROJECT",
        created_at=datetime.utcnow(),
    )
    db_session.add_all([task, project])
    db_session.commit()

    task_review = AIReview(
        task_id=task.id,
        owner_uid=TEST_UID,
        is_active=True,
        comment=json.dumps({"verdict": "t", "score": 5, "questions": []}),
    )
    project_review = AIReview(
        project_id=project.id,
        owner_uid=TEST_UID,
        is_active=True,
        comment=json.dumps({"verdict": "p", "score": 5, "questions": []}),
    )
    db_session.add_all([task_review, project_review])
    db_session.commit()

    _deactivate_active_reviews(db_session, TEST_UID, task_id=task.id)
    db_session.commit()

    db_session.refresh(task_review)
    db_session.refresh(project_review)
    assert task_review.is_active is False
    assert project_review.is_active is True


# ---------------------------------------------------------------------------
# get_all_comments (история)
# ---------------------------------------------------------------------------


async def test_get_review_history_returns_all(async_db, task):
    for score in range(3):
        r = AIReview(
            task_id=task.id,
            owner_uid=TEST_UID,
            is_active=(score == 2),
            comment=json.dumps({"verdict": "x", "score": score, "questions": []}),
        )
        async_db.add(r)
    await async_db.commit()

    history = await get_all_comments(async_db, TEST_UID, task_id=task.id)
    assert len(history) == 3


# ---------------------------------------------------------------------------
# get_review_by_id
# ---------------------------------------------------------------------------


async def test_get_review_by_id_wrong_user_returns_none(async_db, active_review):
    result = await get_review_by_id(async_db, active_review.id, OTHER_UID)
    assert result is None
