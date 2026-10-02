"""PERMANENT REGRESSION GUARD — no orphan skills or dependencies.

Observed bug: POST /api/goals/{id}/skills and /skill-dependencies accepted a
nonexistent goal_id (SQLite does not enforce the FK), leaving orphan rows that
silently attached to whichever real goal later reused that id.

The endpoints now require the parent goal to exist (and dependency endpoints
require both skills to belong to that goal). These tests pin that behavior.
Run with DATABASE_URL pointing at a disposable database.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.database import Base, engine, SessionLocal
from models.goal import Goal

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    Base.metadata.create_all(bind=engine)
    yield
    # rows live only in the disposable DATABASE_URL for this run


def _create_goal(title="Guard Goal"):
    return client.post("/api/goals", json={
        "title": title, "hours_per_week": 5, "duration_weeks": 8, "budget": 0,
    }).json()["id"]


def _skill_rows_for(goal_id):
    db = SessionLocal()
    from models.skill import Skill, SkillDependency
    skills = db.query(Skill).filter(Skill.goal_id == goal_id).all()
    deps = db.query(SkillDependency).filter(SkillDependency.goal_id == goal_id).all()
    db.close()
    return skills, deps


def test_skill_creation_for_nonexistent_goal_is_rejected():
    missing = 999999
    r = client.post(f"/api/goals/{missing}/skills",
                    json={"goal_id": missing, "name": "Orphan Skill", "target_level": "Proficient", "importance": 1.0})
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()
    skills, _ = _skill_rows_for(missing)
    assert skills == [], "no orphan skill row may be created for a nonexistent goal"


def test_dependency_creation_for_nonexistent_goal_is_rejected():
    missing = 999999
    r = client.post(f"/api/goals/{missing}/skill-dependencies",
                    json={"goal_id": missing, "prerequisite_skill_id": 1, "dependent_skill_id": 2})
    assert r.status_code == 404
    _, deps = _skill_rows_for(missing)
    assert deps == [], "no orphan dependency row may be created for a nonexistent goal"


def test_dependency_with_skills_from_another_goal_is_rejected():
    g1 = _create_goal("Goal One")
    g2 = _create_goal("Goal Two")
    s1 = client.post(f"/api/goals/{g1}/skills",
                     json={"goal_id": g1, "name": "G1 Skill", "target_level": "Proficient", "importance": 1.0}).json()["id"]

    # g2 tries to reference g1's skill
    r = client.post(f"/api/goals/{g2}/skill-dependencies",
                    json={"goal_id": g2, "prerequisite_skill_id": s1, "dependent_skill_id": s1})
    assert r.status_code == 404
    _, deps = _skill_rows_for(g2)
    assert deps == [], "dependencies may not reference skills outside their goal"


def test_valid_skill_and_dependency_creation_still_work():
    gid = _create_goal("Valid Goal")
    a = client.post(f"/api/goals/{gid}/skills",
                    json={"goal_id": gid, "name": "Skill A", "target_level": "Proficient", "importance": 1.0})
    b = client.post(f"/api/goals/{gid}/skills",
                    json={"goal_id": gid, "name": "Skill B", "target_level": "Proficient", "importance": 1.0})
    assert a.status_code == 201 and b.status_code == 201
    dep = client.post(f"/api/goals/{gid}/skill-dependencies",
                      json={"goal_id": gid, "prerequisite_skill_id": a.json()["id"], "dependent_skill_id": b.json()["id"]})
    assert dep.status_code == 201
    skills, deps = _skill_rows_for(gid)
    assert len(skills) == 2 and len(deps) == 1


def test_orphan_attempt_does_not_attach_to_a_later_reused_goal_id():
    """The exact reported failure mode: an orphan attempt on a not-yet-existing
    id must not leak into the goal that later receives that id."""
    first = _create_goal("First Goal")
    attempted_id = first + 1  # the id the next created goal will receive
    r = client.post(f"/api/goals/{attempted_id}/skills",
                    json={"goal_id": attempted_id, "name": "Premature Skill", "target_level": "Proficient", "importance": 1.0})
    assert r.status_code == 404

    second = _create_goal("Second Goal")
    assert second == attempted_id, "test setup expects sequential ids on a fresh database"
    skills, deps = _skill_rows_for(second)
    assert skills == [] and deps == [], \
        "the reused goal id must start clean — no inherited orphan rows"
