from celery import Celery

from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from app.logging_config import configure_logging

configure_logging()

# Создание экземпляра Celery
celery_app = Celery(
    "lasalsa-tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)


celery_app.conf.task_routes = {
    "app.tasks.build_task_chain": {"queue": "task_chains"},
    "app.tasks.make_ai_tasks_review": {"queue": "ai_reviews"},
}

# import app.crud  # noqa: E402, F401
celery_app.conf.include = [
    "app.crud.task_ai_comment",  # <-- путь к файлу с make_ai_tasks_review
    "app.crud.chains",  # <-- или как называется файл с build_task_chain
]
