import os

from dotenv import load_dotenv

# Выбор .env файла
env_file = {"dev": ".env", "test": ".env.test", "qa": ".env.qa"}.get(
    os.getenv("ENV", "dev"), ".env"
)

# Загрузка переменных окружения из выбранного файла
load_dotenv(env_file, override=True)

# Получение нужных переменных
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
SERVICE_ACCOUNT_KEY_PATH = os.getenv("SERVICE_ACCOUNT_KEY_PATH")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
ORIGINS = os.getenv("ORIGINS", "").split(",")
LLM_API_KEY = os.getenv("LLM_API_KEY")

