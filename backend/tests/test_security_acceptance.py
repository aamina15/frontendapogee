"""Critical acceptance regressions; run against an isolated DATABASE_URL."""
import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from config import settings
from db.database import SessionLocal
from main import app
from models.diagnostic import DiagnosticQuestion
from services.ai_service import generate_skill_dag_with_gemini


@pytest.fixture
def learner(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = TestClient(app)
    goal = client.post("/api/goals", json={
        "title": "Frontend Developer Internship", "hours_per_week": 7,
        "duration_weeks": 8, "budget": 0,
    }).json()["id"]
    graph = client.post(f"/api/goals/{goal}/generate-graph").json()
    root = next(s["db_id"] for s in graph["skills"] if s["status"] == "AVAILABLE")
    mastery = client.post(f"/api/goals/{goal}/mastery", json={
        "goal_id": goal, "skill_id": root, "diagnostic_score": 0.5,
    }).json()["id"]
    return client, goal, root, mastery


@pytest.mark.parametrize("forged", [{"verified": True}, {"verification_score": 1.0}])
def test_public_mastery_cannot_forge_verification(learner, forged):
    client, goal, root, mastery = learner
    assert client.patch(f"/api/goals/{goal}/mastery/{mastery}", json=forged).status_code == 422
    assert client.post(f"/api/goals/{goal}/mastery", json={
        "goal_id": goal, "skill_id": root, **forged,
    }).status_code == 422
    state = client.get(f"/api/goals/{goal}/mastery").json()[0]
    assert state["verified"] is False and state["verification_score"] is None


def test_mastery_requires_matching_goal(learner):
    client, goal, root, mastery = learner
    other = client.post("/api/goals", json={"title": "Another learner goal"}).json()["id"]
    assert client.patch(f"/api/goals/{other}/mastery/{mastery}", json={"diagnostic_score": 1}).status_code == 404
    assert client.post(f"/api/goals/{other}/mastery", json={
        "goal_id": other, "skill_id": root,
    }).status_code == 404
    assert client.get(f"/api/goals/{goal}/mastery").json()[0]["diagnostic_score"] == 0.5


def test_real_grading_still_verifies_and_unlocks_all_prerequisites(learner):
    client, goal, root, mastery = learner
    # Give TypeScript a second prerequisite, React, through the persisted graph.
    from models.skill import SkillDependency
    graph = client.get(f"/api/goals/{goal}/graph").json()
    ids = {s["id"]: s["db_id"] for s in graph["skills"]}
    with SessionLocal() as db:
        db.add(SkillDependency(goal_id=goal, prerequisite_skill_id=ids["react_basics"], dependent_skill_id=ids["typescript"]))
        db.commit()

    for slug in ["html_css", "javascript", "react_basics"]:
        sid = ids[slug]
        quiz = client.post(f"/api/goals/{goal}/skills/{sid}/verification")
        assert quiz.status_code == 200
        with SessionLocal() as db:
            questions = db.query(DiagnosticQuestion).filter(
                DiagnosticQuestion.goal_id == goal, DiagnosticQuestion.skill_slug == f"verif_{sid}"
            ).all()
            answers = [{"question_id": q.id, "selected_option": q.correct_index} for q in questions]
        result = client.post(f"/api/goals/{goal}/skills/{sid}/verify", json={"answers": answers}).json()
        assert result["passed"] and result["skill"]["status"] == "VERIFIED"
        states = client.get(f"/api/goals/{goal}/graph").json()["skills"]
        expected = "AVAILABLE" if slug == "react_basics" else "LOCKED"
        assert next(s["status"] for s in states if s["id"] == "typescript") == expected


@pytest.mark.parametrize("failure", ["http", "exception", "malformed"])
def test_gemini_failures_do_not_log_credentials(monkeypatch, caplog, failure):
    # A sentinel for leakage assertions, never a real credential or live request.
    sentinel = "credential-leak-test-sentinel"
    monkeypatch.setattr(settings, "GEMINI_API_KEY", sentinel)

    def respond(self, url, **kwargs):
        assert sentinel not in url and "?key=" not in url
        assert kwargs["headers"]["x-goog-api-key"] == sentinel
        if failure == "exception":
            raise httpx.ConnectError(sentinel)
        if failure == "http":
            return httpx.Response(403, text=sentinel)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": sentinel}]}}]})

    monkeypatch.setattr(httpx.Client, "post", respond)
    with caplog.at_level(logging.WARNING):
        result = generate_skill_dag_with_gemini("Frontend Developer Internship")
    assert result["source"] == "fallback" and result["warning"]
    assert sentinel not in caplog.text
