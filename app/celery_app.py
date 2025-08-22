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
}

import app.crud  # noqa: E402, F401
