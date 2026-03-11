"""
Тесты Celery-тасков для AI Review.

Таски запускаются синхронно через celery_eager (autouse).
LLM мокируется, сессия БД подменяется через monkeypatch.
"""

import json
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.crud.ai_review import run_project_review, run_task_review
from app.models import AIReview, Project, Task
from app.services.llm import LLMError

TEST_UID = "test_user_123"

FAKE_COMMENT = {"verdict": "Тест", "score": 7, "questions": ["Вопрос?"]}


# ---------------------------------------------------------------------------
# Вспомогательная утилита: оборачиваем db_session в CM без закрытия сессии
# ---------------------------------------------------------------------------


def _session_cm(session):
    @contextmanager
    def _cm():
        yield session

    return _cm()


# ---------------------------------------------------------------------------
# Фикстуры данных (только для этого файла, используют db_session)
# ---------------------------------------------------------------------------


@pytest.fixture
def task(db_session):
    t = Task(
        name="Тестовая задача",
        owner_uid=TEST_UID,
        status="TODO",
        created_at=datetime.utcnow(),
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def active_review(db_session, task):
    r = AIReview(
        task_id=task.id,
        owner_uid=TEST_UID,
        is_active=True,
        comment=json.dumps({"verdict": "Старое", "score": 5, "questions": []}),
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


@pytest.fixture
def project(db_session):
    p = Project(
        name="Тестовый проект",
        owner_uid=TEST_UID,
        status="ACTIVE",
        type="LIST",
        created_at=datetime.utcnow(),
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def task_with_project(db_session, project):
    t = Task(
        name="Задача в проекте",
        owner_uid=TEST_UID,
        status="TODO",
        created_at=datetime.utcnow(),
        project_id=project.id,
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def active_project_review(db_session, project):
    r = AIReview(
        project_id=project.id,
        owner_uid=TEST_UID,
        is_active=True,
        comment=json.dumps(
            {"verdict": "Старое проектное", "score": 4, "questions": []}
        ),
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


# ---------------------------------------------------------------------------
# Тесты
# ---------------------------------------------------------------------------


def test_run_task_review_saves_review(db_session, task):
    with (
        patch("app.crud.ai_review.llm.get_task_review", return_value=FAKE_COMMENT),
        patch(
            "app.crud.ai_review.get_sync_session",
            side_effect=lambda: _session_cm(db_session),
        ),
    ):
        run_task_review.apply(args=[TEST_UID, task.id])

    reviews = (
        db_session.execute(
            select(AIReview).where(AIReview.task_id == task.id, AIReview.is_active)
        )
        .scalars()
        .all()
    )
    assert len(reviews) == 1


def test_run_task_review_deactivates_previous(db_session, task, active_review):
    with (
        patch(
            "app.crud.ai_review.llm.get_task_review",
            return_value={"verdict": "Новое", "score": 8, "questions": []},
        ),
        patch(
            "app.crud.ai_review.get_sync_session",
            side_effect=lambda: _session_cm(db_session),
        ),
    ):
        run_task_review.apply(args=[TEST_UID, task.id])

    db_session.expire_all()
    all_reviews = (
        db_session.execute(select(AIReview).where(AIReview.task_id == task.id))
        .scalars()
        .all()
    )
    active = [r for r in all_reviews if r.is_active]
    inactive = [r for r in all_reviews if not r.is_active]

    assert len(all_reviews) == 2
    assert len(active) == 1
    assert len(inactive) == 1
    assert inactive[0].id == active_review.id


def test_run_task_review_llm_error_keeps_previous(db_session, task, active_review):
    with (
        patch(
            "app.crud.ai_review.llm.get_task_review",
            side_effect=LLMError("недоступен"),
        ),
        patch(
            "app.crud.ai_review.get_sync_session",
            side_effect=lambda: _session_cm(db_session),
        ),
        pytest.raises(LLMError),
    ):
        run_task_review.apply(args=[TEST_UID, task.id], throw=True)

    db_session.expire_all()
    db_session.refresh(active_review)
    assert active_review.is_active is True


def test_run_task_review_invalid_json_keeps_previous(db_session, task, active_review):
    with (
        patch(
            "app.crud.ai_review.llm.get_task_review",
            side_effect=json.JSONDecodeError("", "", 0),
        ),
        patch(
            "app.crud.ai_review.get_sync_session",
            side_effect=lambda: _session_cm(db_session),
        ),
        pytest.raises(json.JSONDecodeError),
    ):
        run_task_review.apply(args=[TEST_UID, task.id], throw=True)

    db_session.expire_all()
    db_session.refresh(active_review)
    assert active_review.is_active is True


def test_run_task_review_with_project(db_session, task_with_project, project):
    """Задача с проектом: project_name передаётся в LLM."""
    captured = []

    def _capture(task_name, project_name=None):
        captured.append(project_name)
        return FAKE_COMMENT

    with (
        patch("app.crud.ai_review.llm.get_task_review", side_effect=_capture),
        patch(
            "app.crud.ai_review.get_sync_session",
            side_effect=lambda: _session_cm(db_session),
        ),
    ):
        run_task_review.apply(args=[TEST_UID, task_with_project.id])

    assert captured[0] == project.name


# ---------------------------------------------------------------------------
# run_project_review
# ---------------------------------------------------------------------------

FAKE_PROJECT_COMMENT = {"verdict": "Проект ОК", "score": 8, "questions": []}


def test_run_project_review_saves_review(db_session, project):
    with (
        patch(
            "app.crud.ai_review.llm.get_project_review",
            return_value=FAKE_PROJECT_COMMENT,
        ),
        patch(
            "app.crud.ai_review.get_sync_session",
            side_effect=lambda: _session_cm(db_session),
        ),
    ):
        run_project_review.apply(args=[TEST_UID, project.id])

    reviews = (
        db_session.execute(
            select(AIReview).where(
                AIReview.project_id == project.id, AIReview.is_active
            )
        )
        .scalars()
        .all()
    )
    assert len(reviews) == 1


def test_run_project_review_deactivates_previous(
    db_session, project, active_project_review
):
    with (
        patch(
            "app.crud.ai_review.llm.get_project_review",
            return_value={"verdict": "Новое", "score": 9, "questions": []},
        ),
        patch(
            "app.crud.ai_review.get_sync_session",
            side_effect=lambda: _session_cm(db_session),
        ),
    ):
        run_project_review.apply(args=[TEST_UID, project.id])

    db_session.expire_all()
    all_reviews = (
        db_session.execute(select(AIReview).where(AIReview.project_id == project.id))
        .scalars()
        .all()
    )
    active = [r for r in all_reviews if r.is_active]
    inactive = [r for r in all_reviews if not r.is_active]

    assert len(all_reviews) == 2
    assert len(active) == 1
    assert len(inactive) == 1
    assert inactive[0].id == active_project_review.id
