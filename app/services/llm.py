import json

import openai
from celery.utils.log import get_task_logger

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_PROJECT, LLM_PROMPT_ID

logger = get_task_logger(__name__)

class LLMError(Exception):
    pass

class LLM:
    def __init__(self) -> None:
        self.client = openai.OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            project=LLM_PROJECT,
        )

    def get_task_review(self, task_name: str, project_name: str = None) -> str:
        project_part = f"из проекта «{project_name}» " if project_name else ""
        # Составляем запрос
        query_input = (
            f"Применяя правила GTD и Джедайских техник дай комментарий к задаче "
            f"«{task_name}» {project_part}"
            f"и отдай в виде JSON со следующими полями: "
            f"`verdict` — одна фраза, общий вывод, "
            f"`score` — int от 1 до 10, соответствие GTD, "
            f"`questions` — список строк, конкретные проблемы (может быть пустым)"
        )
        return self._get_llm_response(query_input)

    def _get_llm_response(self, query_input: str) -> str:
        try:
            response = self.client.responses.create(
                prompt={"id": LLM_PROMPT_ID},
                input=query_input,
            )
            logger.info(f"Response from LLM: {response}")
            return self._parse_llm_response(response.output_text)
        except openai.OpenAIError as e:
            logger.error(f"LLM request failed: {e}")
            raise LLMError(f"LLM недоступен: {e}") from e

    def _parse_llm_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    def get_project_review(
        self,
        project_name: str,
        active_tasks: list[str],
        total_tasks: int,
        completed_tasks: int,
    ) -> str:
        tasks_list = "\n".join(f"- {task}" for task in active_tasks[:30])
        query_input = (
            f"Посмотри на проект «{project_name}».\n"
            f"Всего задач: {total_tasks}, из них выполнено: {completed_tasks}, "
            f"активных показано: {min(len(active_tasks), 30)}.\n"
            f"Активные задачи:\n{tasks_list}\n"
            f"Оцени структуру проекта: есть ли задачи которые на самом деле являются проектами, "
            f"что выглядит размыто или застрявшим.\n"
            f"Верни JSON: verdict — одна фраза, score — int 1-10 насколько проект декомпозирован, "
            f"questions — список вопросов к пользователю.\n"
            f"Верни ТОЛЬКО валидный JSON без markdown-блоков и без пояснений."
        )

        return self._get_llm_response(query_input)
