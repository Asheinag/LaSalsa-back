import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base, get_async_session, get_sync_session
from app.dependencies import verify_firebase_token
from app.main import app
from app.celery_app import celery_app

print("== ROUTES ==")
for route in app.routes:
    print(route.path) # type: ignore




@pytest.fixture(scope="function")
async def client():
    TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/test_db"
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_async_session():
        async with session_maker() as session:
            yield session
    
    async def override_verify_firebase_token():
        user = {'uid': 'test_user_123'}
        yield user

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token

    # Очистка БД — до теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # сам клиент
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Очистка БД — после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

# Создание окружения для Celery
SYNC_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5433/test_db"

sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=sync_engine)

@pytest.fixture(autouse=True)
def celery_eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = True 
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_store_eager_result = False


# @pytest.fixture(autouse=True, scope="function")
# def clear_test_redis():
#     r = redis.Redis(host="localhost", port=6380, db=0)
#     r.flushall()
#     yield
#     r.flushall()