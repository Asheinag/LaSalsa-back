import json

import openai
from celery.utils.log import get_task_logger

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_PROJECT, LLM_PROMPT_ID

logger = get_task_logger(__name__)


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
            f"`issues` — список строк, конкретные проблемы (может быть пустым)"
        )
        response = self.client.responses.create(
            prompt={
                "id": LLM_PROMPT_ID,
            },
            input=query_input,
        )
        return self._parse_llm_response(response.output_text)

    def _parse_llm_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
