"""Provider-chain tests. All HTTP responses are mocked; no paid API calls run here."""
from types import SimpleNamespace
import json

import httpx
import pytest
import logging

from config import settings
from services.ai_service import generate_skill_dag_with_gemini
from services.question_service import propose_questions_with_source, questions_for_skills


def dag_payload(name="Python Fundamentals"):
    return {
        "skills": [{"id": "python", "name": name, "target_level": "Proficient", "importance": 1.0}],
        "dependencies": [],
    }


def openai_response(payload):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(payload)}}]})


@pytest.fixture(autouse=True)
def provider_settings(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "test-openai-model")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "test-gemini-model")


def test_openai_success_returns_openai_source(monkeypatch):
    calls = []

    def post(self, url, **kwargs):
        calls.append((url, kwargs))
        return openai_response(dag_payload())

    monkeypatch.setattr(httpx.Client, "post", post)
    result = generate_skill_dag_with_gemini("Learn Python")

    assert result["source"] == "openai"
    assert result["warning"] is None
    assert calls[0][0] == "https://api.openai.com/v1/chat/completions"
    assert calls[0][1]["json"]["model"] == "test-openai-model"
    assert "openai-test-key" not in repr(calls[0][1]["json"])
    assert calls[0][1]["headers"]["Authorization"] == "Bearer openai-test-key"


def test_openai_malformed_response_tries_gemini(monkeypatch):
    calls = []

    def post(self, url, **kwargs):
        calls.append(url)
        if "api.openai.com" in url:
            return openai_response({"not": "a dag"})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(dag_payload("Gemini Python"))}]}}]})

    monkeypatch.setattr(httpx.Client, "post", post)
    result = generate_skill_dag_with_gemini("Learn Python")

    assert result["source"] == "gemini"
    assert calls == [
        "https://api.openai.com/v1/chat/completions",
        "https://generativelanguage.googleapis.com/v1beta/models/test-gemini-model:generateContent",
    ]


def test_provider_failures_use_deterministic_fallback(monkeypatch):
    def post(self, url, **kwargs):
        return httpx.Response(503, text="provider unavailable")

    monkeypatch.setattr(httpx.Client, "post", post)
    result = generate_skill_dag_with_gemini("Frontend Developer")

    assert result["source"] == "fallback"
    assert result["warning"]
    assert result["skills"]


def test_openai_failure_logs_no_credential(monkeypatch, caplog):
    sentinel = "openai-secret-sentinel"
    monkeypatch.setattr(settings, "OPENAI_API_KEY", sentinel)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(httpx.Client, "post", lambda self, url, **kwargs: httpx.Response(401, text=sentinel))

    with caplog.at_level(logging.WARNING):
        generate_skill_dag_with_gemini("Learn Python")

    assert sentinel not in caplog.text


def test_openai_question_proposal_is_validated_and_tagged(monkeypatch):
    skill = SimpleNamespace(id=1, name="Python Programming", slug="python", target_level="Proficient")
    raw = {"questions": [{
        "skill_id": 1,
        "target_level": "Proficient",
        "question": "In Python, what does a list comprehension create?",
        "options": ["A list", "A database", "A socket", "A thread"],
        "correct_index": 0,
        "answer_text": "A list",
        "explanation": "A list comprehension constructs a list from an iterable.",
    }]}
    monkeypatch.setattr(httpx.Client, "post", lambda self, url, **kwargs: openai_response(raw))

    proposals, source = propose_questions_with_source(
        SimpleNamespace(title="Learn Python"), [skill], {1: 1}, [], "diagnostic"
    )

    assert source == "openai"
    assert proposals[1][0]["answer_text"] == "A list"


def test_malformed_question_proposal_uses_curated_bank(monkeypatch):
    skill = SimpleNamespace(id=1, name="Python Programming", slug="python", target_level="Proficient")
    monkeypatch.setattr(httpx.Client, "post", lambda self, url, **kwargs: openai_response({"questions": "bad"}))

    result = questions_for_skills(
        SimpleNamespace(title="Learn Python"), [skill], {1: 1}, [], "verification"
    )

    assert result[1]
    assert result[1][0]["explanation"].startswith("[orbit-assessment:curated]")
