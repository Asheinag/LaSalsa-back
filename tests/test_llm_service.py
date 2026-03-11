"""
Unit-тесты для LLM-сервиса.

HTTP-клиент мокируется — реальных запросов нет.
Тестируем _parse_llm_response и контент промптов через мок _get_llm_response.
"""

import json
from unittest.mock import patch

import pytest

from app.services.llm import LLM, LLMError

FAKE_RESULT = {"verdict": "test", "score": 7, "questions": []}


# ---------------------------------------------------------------------------
# _parse_llm_response
# ---------------------------------------------------------------------------


def test_parse_llm_response_clean_json():
    llm = LLM()
    result = llm._parse_llm_response('{"verdict": "test", "score": 7, "questions": []}')
    assert result["score"] == 7


def test_parse_llm_response_strips_markdown():
    llm = LLM()
    result = llm._parse_llm_response(
        '```json\n{"verdict": "test", "score": 7, "questions": []}\n```'
    )
    assert result["verdict"] == "test"


def test_parse_llm_response_invalid_raises():
    llm = LLM()
    with pytest.raises(json.JSONDecodeError):
        llm._parse_llm_response("не json")


# ---------------------------------------------------------------------------
# Контент промпта для задачи
# ---------------------------------------------------------------------------


def test_get_task_review_prompt_with_project():
    llm = LLM()
    captured = []

    def _capture(query_input):
        captured.append(query_input)
        return FAKE_RESULT

    with patch.object(llm, "_get_llm_response", side_effect=_capture):
        llm.get_task_review("Купить принтер", "Офис")

    assert "Купить принтер" in captured[0]
    assert "Офис" in captured[0]


def test_get_task_review_prompt_without_project():
    llm = LLM()
    captured = []

    def _capture(query_input):
        captured.append(query_input)
        return FAKE_RESULT

    with patch.object(llm, "_get_llm_response", side_effect=_capture):
        llm.get_task_review("Купить принтер", None)

    assert "Купить принтер" in captured[0]
    assert "из проекта" not in captured[0]


# ---------------------------------------------------------------------------
# Контент промпта для проекта
# ---------------------------------------------------------------------------


def test_get_project_review_prompt_limits_tasks():
    llm = LLM()
    captured = []

    def _capture(query_input):
        captured.append(query_input)
        return FAKE_RESULT

    with patch.object(llm, "_get_llm_response", side_effect=_capture):
        tasks = [f"Задача {i}" for i in range(50)]
        llm.get_project_review(
            "Проект", active_tasks=tasks, total_tasks=50, completed_tasks=10
        )

    # В промпте не более 30 задач (active_tasks[:30])
    assert captured[0].count("Задача") <= 30


# ---------------------------------------------------------------------------
# _get_llm_response: обработка ошибок OpenAI
# ---------------------------------------------------------------------------


def test_get_llm_response_raises_llm_error_on_openai_error():
    import openai

    llm = LLM()
    with (
        patch.object(
            llm.client.responses,
            "create",
            side_effect=openai.OpenAIError("service unavailable"),
        ),
        pytest.raises(LLMError),
    ):
        llm._get_llm_response("тестовый запрос")
