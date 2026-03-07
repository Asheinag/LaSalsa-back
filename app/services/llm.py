from app.config import LLM_API_KEY


async def get_task_review(task_name: str, project_name: str = None) -> str:
    # Если у задачи есть ссылка на проект, то в запросе должен быть и он
    if LLM_API_KEY:
        pass

    project_part = f"из проекта «{project_name}» " if project_name else ""

    # Составляем запрос
    query = (
        f"Применяя правила GTD и Джедайских техник дай комментарий к задаче "
        f"«{task_name}» {project_part}"
        f"и отдай в виде JSON со следующими полями: "
        f"`verdict` — одна фраза, общий вывод, "
        f"`score` — int от 1 до 10, соответствие GTD, "
        f"`issues` — список строк, конкретные проблемы (может быть пустым)"
    )

    return query
