from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import get_sync_session
from app.models import Task


@celery_app.task(name="app.tasks.build_task_chain")
def build_task_chain(task_id: int):
    print(f"[TASK] Starting task for task_id={task_id}")
    try:
        with get_sync_session() as session:
            result = collect_chain(session, task_id)
            return result
    except Exception as e:
        print(f"[TASK] Error in task for task_id={task_id}: {e}")
        raise e


def collect_chain(session: Session, task_id: int):
    def recurse(current_id: int) -> dict:
        task: Task = session.query(Task).filter(Task.id == current_id).first()  # type: ignore
        if not task:
            return {}

        subtasks = session.query(Task).filter(Task.parent_id == current_id).all()
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status,
            "planned_at": task.planned_at,
            "closed_at": task.closed_at,
            "project_id": task.project_id,
            "children": [recurse(t.id) for t in subtasks],
        }

    return recurse(task_id)
