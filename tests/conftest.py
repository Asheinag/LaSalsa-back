import os
from typing import Callable, Coroutine

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

# Получи путь к корню проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_file_path = os.path.join(project_root, ".env.test")

# Загрузи .env.test с полным путем
load_dotenv(env_file_path, override=True)

# Используем переменные напрямую из os.environ
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

print(
    f"DB_HOST: {DB_HOST}, DB_USER: {DB_USER}, DB_NAME: {DB_NAME}, DB_PORT: {DB_PORT}, DB_PASS: {DB_PASS}"
)

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


print("== ROUTES ==")
for route in app.routes:
    print(route.path)  # type: ignore


@pytest.fixture(scope="function")
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_async_session():
        async with session_maker() as session:
            yield session

    async def override_verify_firebase_token():
        user = {"uid": "test_user_123"}
        yield user

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token

    # Очистка БД — до теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # сам клиент
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Очистка БД — после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
    session = SyncSessionLocal()
    try:
        # Устанавливаем тестовую сессию глобально
        global _test_sync_session
        _test_sync_session = session
        yield session
    finally:
        session.close()
        _test_sync_session = None  # Сбрасываем после теста
        Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture(autouse=True)
def celery_eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = True
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_store_eager_result = False


@pytest.fixture
def mock_celery_session(db_session, monkeypatch):
    # Мокаем функцию, которая возвращает сессию
    def get_test_session():
        return db_session

    # Мокаем правильный путь к функции
    monkeypatch.setattr("app.database.get_sync_session", get_test_session)
    # Также мокаем в модуле celery_app, если там импортируется по-другому
    monkeypatch.setattr("app.celery_app.get_sync_session", get_test_session)


@pytest.fixture
def create_project_factory(client: AsyncClient) -> Callable[..., Coroutine]:
    """
    Фикстура-фабрика для создания задачи.
    Возвращает саму асинхронную функцию.
    """

    async def _create_project(project_name: str = "Test Project"):
        return await client.post(
            "/projects/",
            json={
                "name": project_name,
            },
        )

    return _create_project


@pytest.fixture
def create_task_factory(client: AsyncClient) -> Callable[..., Coroutine]:
    """
    Фикстура-фабрика для создания задачи.
    Возвращает саму асинхронную функцию.
    """

    async def _create_task(task_data=None):
        if task_data is None:
            task_data = {
                "name": "Test Task",
                "description": "Created via test",
                "status": "TODO",
            }
        return await client.post("/tasks/", json=task_data)

    return _create_task
