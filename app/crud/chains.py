from sqlalchemy import UUID
from app.celery_app import celery_app
from app.database import get_sync_session
from app.models import Task
from sqlalchemy.orm import Session

@celery_app.task(name="app.tasks.build_task_chain")
def build_task_chain(task_id: UUID):
    print(f"[TASK] Starting task for task_id={task_id}")
    try:
        with get_sync_session() as session:
            result = collect_chain(session, task_id)
            return result
    except Exception as e:
        print(f"[TASK] Error in task for task_id={task_id}: {e}")
        raise e
    

def collect_chain(session: Session, task_id: UUID):
    def recurse(current_id):
        subtasks = session.query(Task).filter(Task.parent_id == current_id).all()
        return {
            "id": str(current_id),  # 👈 вот тут
            "children": [recurse(t.id) for t in subtasks]
        }

    return recurse(task_id)