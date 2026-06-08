import json
import os
from collections.abc import Callable, Coroutine

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.database import Base, get_async_session
from app.dependencies import verify_firebase_token
from app.main import app
from app.models import AIReview, RecurringFrequency

# Загружаем .env.test только если мы НЕ в CI
if not os.getenv("CI"):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file_path = os.path.join(project_root, ".env.test")
    load_dotenv(env_file_path, override=True)

# Теперь берем переменные (они придут либо из .env.test локально, либо из YAML в CI)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "test_db")
DB_PORT = os.getenv("DB_PORT", "5432")


# Формируем строки подключения
# Асинхронная строка подключения для тестов
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
# Синхронная строка подключения для фикстур с синхронной сессией
SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


@pytest.fixture(scope="function")
async def client():
    """
    Фикстура для асинхронного клиента HTTPX с переопределенными зависимостями.
    """
    # Создаем асинхронный движок и сессию
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # Переопределяем зависимости
    async def override_get_async_session():
        async with session_maker() as session:
            yield session

    async def override_verify_firebase_token():
        user = {"uid": "test_user_123"}
        yield user

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token

    # Очищаем БД — до теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Создаем клиент HTTPX
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Очищаем переопределения после теста, чтобы не влиять на другие
    del app.dependency_overrides[get_async_session]
    del app.dependency_overrides[verify_firebase_token]
    # Очищаем БД — после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def unauthenticated_client():
    """
    Фикстура для анонимного клиента, который НЕ переопределяет
    зависимость аутентификации.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # Переопределяем ТОЛЬКО зависимость базы данных
    async def override_get_async_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Очищаем переопределение после теста, чтобы не влиять на другие
    del app.dependency_overrides[get_async_session]

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# Глобальная переменная для хранения тестовой синхронной сессии
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Фикстура для синхронной сессии базы данных.
    """
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
    session = SyncSessionLocal()
    # Устанавливаем тестовую сессию глобально
    try:
        global _test_sync_session
        _test_sync_session = session
        yield session
    finally:
        session.close()
        _test_sync_session = None
        Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture(autouse=True)
def celery_eager():
    """
    Фикстура для выполнения задач Celery синхронно в тестах.
    """
    # Включаем режим eager
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = True
    yield
    # Выключаем режим eager
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_store_eager_result = False


@pytest.fixture
def mock_celery_session(db_session, monkeypatch):
    """
    Фикстура для мока сессии базы данных в задачах Celery.
    """

    # Мокаем функцию, которая возвращает сессию
    def get_test_session():
        return db_session

    # Мокаем правильный путь к функции
    monkeypatch.setattr("app.database.get_sync_session", get_test_session)
    # Также мокаем в модуле celery_app, если там импортируется по-другому
    monkeypatch.setattr("app.crud.recurring_task.get_sync_session", get_test_session)


@pytest.fixture
def create_project_factory(client: AsyncClient) -> Callable[..., Coroutine]:
    """
    Фикстура-фабрика для создания задачи.
    Возвращает саму асинхронную функцию.
    """

    # Функция для создания проекта
    async def _create_project(project_data: dict = None):
        if project_data is None:
            project_data = {
                "name": "Test Project",
                "description": "Created via test",
                "status": "INACTIVE",
                "color_id": 1,
            }
        return await client.post(
            "/projects/",
            json=project_data,
        )

    return _create_project


@pytest.fixture
def create_task_factory(client: AsyncClient) -> Callable[..., Coroutine]:
    """
    Фикстура-фабрика для создания задачи.
    Возвращает саму асинхронную функцию.
    """

    # Функция для создания задачи
    async def _create_task(task_data=None):
        if task_data is None:
            task_data = {
                "name": "Test Task",
                "description": "Created via test",
                "status": "TODO",
            }
        return await client.post("/tasks/", json=task_data)

    return _create_task


@pytest.fixture
def create_pomodoro_factory(client: AsyncClient) -> Callable[..., Coroutine]:
    """
    Фикстура-фабрика для создания сеанса Помодоро.
    Возвращает саму асинхронную функцию.
    """

    # Функция для создания сеанса Помодоро
    async def _create_pomodoro(pomodoro_data=None):
        if pomodoro_data is None:
            pomodoro_data = {
                "note": "Test Pomodoro",
                "duration_minutes": 25,
            }
        return await client.post("/pomodoros/", json=pomodoro_data)

    return _create_pomodoro


@pytest.fixture
async def async_db():
    """
    Асинхронная сессия БД для тестов CRUD-функций.
    Управляет схемой самостоятельно, не зависит от client/db_session.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def create_review_factory(db_session):
    def _create_review(task_id: int, is_active: bool = True):
        review = AIReview(
            task_id=task_id,
            owner_uid="test_user_123",
            is_active=is_active,
            comment=json.dumps(
                {"verdict": "Test verdict", "score": 7, "questions": ["Question 1?"]}
            ),
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        return review

    return _create_review


@pytest.fixture
def create_project_review_factory(db_session):
    def _create_project_review(project_id: int, is_active: bool = True):
        review = AIReview(
            project_id=project_id,
            owner_uid="test_user_123",
            is_active=is_active,
            comment=json.dumps(
                {"verdict": "Test verdict", "score": 7, "questions": ["Question 1?"]}
            ),
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        return review

    return _create_project_review


@pytest.fixture
def create_recurring_task_factory(client: AsyncClient) -> Callable[..., Coroutine]:
    """
    Фикстура-фабрика для создания задачи.
    Возвращает саму асинхронную функцию.
    """

    # Функция для создания задачи
    async def _create_recurring_task_factory(recurring_task_data=None):
        if recurring_task_data is None:
            recurring_task_data = {
                "name": "Test Recurring Task",
                "description": "Created via test",
                "frequency": RecurringFrequency.DAILY,
                "days": [],
                "timezone": "UTC",
                "task_id": 1,
            }
        return await client.post("/recurring-tasks/", json=recurring_task_data)

    return _create_recurring_task_factory
