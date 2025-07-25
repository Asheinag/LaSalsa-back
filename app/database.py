from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER  # noqa: E402

# 👇 Настройка подключения (проверь путь!)
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL_SYNC = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# 👇 Асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# 👇 Синхронный движок (для Celery и других синхронных задач
sync_engine = create_engine(DATABASE_URL_SYNC, echo=False)

# 👇 Сессионный фабрикат для асинхронных операций
sync_sessionmaker = sessionmaker(bind=sync_engine, expire_on_commit=False)

# 👇 Асинхронный сессионный фабрикат
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# 👇 Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# 👇 Зависимость для FastAPI (yield, а не return!)
async def get_async_session():
    async with async_session_maker() as session:
        yield session

# 👇 Зависимость для синхронных операций (например, Celery)
def get_sync_session():
    return sync_sessionmaker()
