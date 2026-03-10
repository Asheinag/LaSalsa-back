from typing import Any

from celery import Celery
from celery.result import AsyncResult

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
    "app.tasks.make_ai_task_review": {"queue": "ai_reviews"},
    "app.tasks.make_ai_project_review": {"queue": "ai_reviews"},
}

# import app.crud  # noqa: E402, F401
celery_app.conf.include = [
    "app.crud.ai_review",  # <-- путь к файлу с make_ai_review
    "app.crud.chains",  # <-- или как называется файл с build_task_chain
]


def get_celery_task_status(celery_task_id: str) -> dict[str, Any]:  # noqa: B008
    """
    Эндпоинт для запроса статуса задачи поставленной на Celery
    """
    result = AsyncResult(celery_task_id, app=celery_app)

    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "done", "data": result.result}
    elif result.state == "FAILURE":
        return {"status": "error", "reason": str(result.result)}
    else:
        return {"status": result.state}
