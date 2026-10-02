"""PERMANENT REGRESSION GUARD — Capability Map / route-creation invariant.

Background: the Capability Map once resolved missing skill resources through
GET /api/goals/{id}/route — a get-or-create endpoint. Merely inspecting the
map therefore created an "Initial route" row, materialized resource rows, and
(via App.restore's canRoute = routes.length > 0) prematurely unlocked the
Build Route / Learn & Verify stages on refresh.

The fix resolves map resources through the READ-ONLY per-skill catalogue
fallback (GET /api/skills/{id}/resources). These tests pin the invariant:

    Opening and inspecting the Capability Map is side-effect-free with
    respect to routes, route versions, resource materialization, and mastery.

They also document, in test H, that GET /api/goals/{id}/route is get-or-create
by design — so any code path that calls it from a read-only surface WILL trip
the assertions here. Run with DATABASE_URL pointing at a disposable database.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.database import Base, engine, SessionLocal
from models.goal import Goal
from services.resource_service import (
    VERIFIED_RESOURCE_CATALOGUE,
    VERIFIED_VIDEO_CATALOGUE,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def goal_with_graph(monkeypatch):
    """One goal with a generated graph and a provably untouched database."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    goal = Goal(title="Frontend Developer Internship", hours_per_week=7.0,
                duration_weeks=12, budget=0.0, status="active")
    db.add(goal)
    db.commit()
    db.refresh(goal)
    goal_id = goal.id
    db.close()

    res = client.post(f"/api/goals/{goal_id}/generate-graph")
    assert res.status_code == 200, res.text
    yield goal_id


def _raw_counts(goal_id):
    """Count rows THROUGH SQL, scoped to this goal, so side effects cannot
    hide behind API responses or other tests' rows in the shared run DB."""
    db = SessionLocal()
    from sqlalchemy import text
    out = {}
    out["routes"] = db.execute(text(
        "SELECT COUNT(*) FROM routes WHERE goal_id = :g"), {"g": goal_id}).scalar()
    out["masteries"] = db.execute(text(
        "SELECT COUNT(*) FROM masteries WHERE goal_id = :g"), {"g": goal_id}).scalar()
    out["resources"] = db.execute(text(
        "SELECT COUNT(*) FROM resources WHERE skill_id IN "
        "(SELECT id FROM skills WHERE goal_id = :g)"), {"g": goal_id}).scalar()
    out["versions"] = [r[0] for r in db.execute(text(
        "SELECT version FROM routes WHERE goal_id = :g ORDER BY version"), {"g": goal_id}).fetchall()]
    out["reasons"] = [r[0] for r in db.execute(text(
        "SELECT change_reason FROM routes WHERE goal_id = :g ORDER BY version"), {"g": goal_id}).fetchall()]
    db.close()
    return out


def _skill_ids(goal_id):
    db = SessionLocal()
    from models.skill import Skill
    ids = [s.id for s in db.query(Skill).filter(Skill.goal_id == goal_id).order_by(Skill.id).all()]
    db.close()
    return ids


# ===== A. Graph creation alone is side-effect-free ===========================

def test_graph_generation_creates_no_routes_resources_or_mastery(goal_with_graph):
    goal_id = goal_with_graph
    counts = _raw_counts(goal_id)
    assert counts["routes"] == 0, "graph generation must not create route rows"
    assert counts["resources"] == 0, "graph generation must not materialize resources"
    assert counts["masteries"] == 0, "graph generation must not create mastery rows"


# ===== B. The map's exact request inventory is side-effect-free ==============

def test_capability_map_request_inventory_is_side_effect_free(goal_with_graph):
    """Replay EXACTLY the requests the Capability Map makes (graph, mastery,
    routes LIST, per-skill resources, graph refresh). None may write."""
    goal_id = goal_with_graph
    skills = client.get(f"/api/goals/{goal_id}/graph").json()["skills"]
    assert skills, "graph must exist for this scenario"

    client.get(f"/api/goals/{goal_id}/graph")                     # map load
    client.get(f"/api/goals/{goal_id}/diagnostic/mastery")        # mastery overlay
    client.get(f"/api/goals/{goal_id}/routes")                    # READ-ONLY list (allowed)
    for s in skills:
        r = client.get(f"/api/skills/{s['db_id']}/resources")     # catalogue fallback
        assert r.status_code == 200, r.text
    client.get(f"/api/goals/{goal_id}/graph")                     # Refresh Graph button

    counts = _raw_counts(goal_id)
    assert counts["routes"] == 0, "map exploration must not create route rows"
    assert counts["resources"] == 0, "map exploration must not materialize resources"
    assert counts["masteries"] == 0, "map exploration must not create mastery rows"


# ===== C. Per-skill resource fallback: genuine catalogue data, read-only =====

def test_resource_fallback_returns_real_catalogue_before_any_route(goal_with_graph):
    from services.resource_service import find_verified_resource_for_skill
    goal_id = goal_with_graph
    db = SessionLocal()
    from models.skill import Skill
    html = db.query(Skill).filter(Skill.goal_id == goal_id, Skill.slug == "html_css").first()
    db.close()
    assert html is not None

    r = client.get(f"/api/skills/{html.id}/resources")
    assert r.status_code == 200
    entries = r.json()
    assert entries, "a catalogue skill must surface real resources before any route exists"

    reading = next(e for e in entries if e["format"] == "reading")
    expected = VERIFIED_RESOURCE_CATALOGUE["html_css"]
    assert reading["title"] == expected["title"]
    assert reading["url"] == expected["url"]
    assert reading["source"] == expected["source"]
    assert reading["duration_hours"] == expected["duration_hours"]

    video = next(e for e in entries if e["format"] == "video")
    expected_v = VERIFIED_VIDEO_CATALOGUE["html_css"]
    assert video["title"] == expected_v["title"]
    assert video["url"] == expected_v["url"]
    assert video["duration_hours"] == expected_v["duration_hours"]

    counts = _raw_counts(goal_id)
    assert counts["routes"] == 0, "resource fallback must not create route rows"
    assert counts["resources"] == 0, "resource fallback must not materialize resource rows"
    assert counts["masteries"] == 0, "resource fallback must not touch mastery"


def test_resource_fallback_is_readonly_and_consistent_on_repeat(goal_with_graph):
    goal_id = goal_with_graph
    sid = _skill_ids(goal_id)[0]
    first = client.get(f"/api/skills/{sid}/resources").json()
    second = client.get(f"/api/skills/{sid}/resources").json()
    third = client.get(f"/api/skills/{sid}/resources").json()
    assert first == second == third, "repeated reads must return consistent data"
    counts = _raw_counts(goal_id)
    assert counts["routes"] == 0 and counts["resources"] == 0 and counts["masteries"] == 0, \
        "repeated resource reads must stay read-only (no duplicates, no route rows)"


def test_skills_without_catalogue_entries_return_empty_not_invented(goal_with_graph):
    from models.skill import Skill
    db = SessionLocal()
    ghost = Skill(goal_id=goal_with_graph, name="Quantum Surfing Mastery", slug="quantum_surfing")
    db.add(ghost)
    db.commit()
    db.refresh(ghost)
    sid = ghost.id
    db.close()

    r = client.get(f"/api/skills/{sid}/resources")
    assert r.status_code == 200
    assert r.json() == [], "skills without catalogue entries must stay honestly empty"
    counts = _raw_counts(goal_with_graph)
    assert counts["routes"] == 0 and counts["resources"] == 0


# ===== D. Explicit Build Route: creation happens HERE, and only here =========

def test_explicit_build_route_creates_route_and_materializes_resources(goal_with_graph):
    goal_id = goal_with_graph
    graph = client.get(f"/api/goals/{goal_id}/graph").json()
    route = client.get(f"/api/goals/{goal_id}/route")   # the explicit Build Route read
    assert route.status_code == 200

    counts = _raw_counts(goal_id)
    assert counts["routes"] == 1, "the explicit route read creates exactly one route"
    assert counts["versions"] == [1] and counts["reasons"] == ["Initial route"]
    assert counts["resources"] > 0, "the planner materializes catalogue resources by design"
    assert counts["masteries"] == 0, "building a route never creates mastery"

    # Prerequisite order remains correct: every dependency's prerequisite
    # appears at or before its dependent in the phase's ordered resources.
    data = route.json()
    ordered_ids = [r["skill_id"] for p in data["phases"] for r in p["resources"]]
    position = {sid: i for i, sid in enumerate(ordered_ids)}
    for dep in graph["dependencies"]:
        pre_db = next(s["db_id"] for s in graph["skills"] if s["id"] == dep["from"])
        dep_db = next(s["db_id"] for s in graph["skills"] if s["id"] == dep["to"])
        assert position[pre_db] <= position[dep_db], \
            f"prerequisite {dep['from']} must precede {dep['to']}"


# ===== E. Repeated route reads with unchanged data: no version churn =========

def test_repeated_route_reads_do_not_duplicate_versions(goal_with_graph):
    goal_id = goal_with_graph
    for _ in range(3):
        r = client.get(f"/api/goals/{goal_id}/route")
        assert r.status_code == 200
    counts = _raw_counts(goal_id)
    assert counts["routes"] == 1 and counts["versions"] == [1], \
        "re-reading an unchanged route must not create new versions"


# ===== F. Route-version stability while the map is open (existing route) =====

def test_map_inspection_does_not_change_an_existing_route_version(goal_with_graph):
    """Opening the Capability Map when a route already exists must leave its
    version untouched — inspection-only, even after route materialization."""
    goal_id = goal_with_graph
    client.get(f"/api/goals/{goal_id}/route")            # route exists now (v1)
    before = _raw_counts(goal_id)
    assert before["versions"] == [1]

    # Map exploration over an existing route
    skills = client.get(f"/api/goals/{goal_id}/graph").json()["skills"]
    client.get(f"/api/goals/{goal_id}/diagnostic/mastery")
    client.get(f"/api/goals/{goal_id}/routes")
    for s in skills:
        client.get(f"/api/skills/{s['db_id']}/resources")

    after = _raw_counts(goal_id)
    assert after["routes"] == 1 and after["versions"] == [1], \
        "inspecting the map must not change an existing route version"
    assert after["resources"] == before["resources"], "no duplicate resource rows"


# ===== G. Tripwires: would these tests catch the old bug? ====================

def test_get_route_is_get_or_create_so_any_map_call_is_detectable(goal_with_graph):
    """Sensitivity proof for the invariant above: GET /api/goals/{id}/route is
    get-or-create BY DESIGN. A single call on a routeless goal immediately
    creates the 'Initial route' row — so if ANY map code path ever calls it
    again, tests B/F fail on the routes count. This test pins that semantics
    so the endpoint cannot silently become 'read-only' either."""
    goal_id = goal_with_graph
    assert _raw_counts(goal_id)["routes"] == 0
    r = client.get(f"/api/goals/{goal_id}/route")
    assert r.status_code == 200
    counts = _raw_counts(goal_id)
    assert counts["routes"] == 1 and counts["versions"] == [1] \
        and counts["reasons"] == ["Initial route"], \
        "GET /route is get-or-create: one call on a routeless goal creates v1"


def test_capability_map_source_never_calls_the_route_planner():
    """Static tripwire: the map component must not import or call
    fetchGoalRoute (GET /api/goals/{id}/route). This is the exact call that
    caused the original bug; if it reappears in the map surface, fail loudly.
    The resource DISPLAY itself is guarded by test C (listResources must stay)."""
    from pathlib import Path
    map_source = Path(__file__).resolve().parents[2] / "src" / "components" / "CompletionGraph.jsx"
    assert map_source.exists(), "Capability Map component missing"
    code = map_source.read_text()
    assert "fetchGoalRoute" not in code, \
        "Capability Map must not call the get-or-create route endpoint"
    assert "listResources" in code, \
        "Capability Map must keep rendering real resources via the read-only endpoint"
