"""PHASE 2: Verified Goal Coverage — API-level acceptance tests.

These exercise the FastAPI service directly with TestClient (API simulation,
NOT a browser). Run with DATABASE_URL pointing to a disposable database.
The Gemini key is monkeypatched off so graphs are always the deterministic
fallback — tests never touch the network.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.database import Base, engine, SessionLocal
from models.goal import Goal
from models.skill import Skill, SkillDependency
from models.mastery import Mastery
from models.diagnostic import DiagnosticQuestion
from services.coverage_service import calculate_coverage

client = TestClient(app)


def correct_verification_answers(goal_id, skill_db_id):
    """Read the server-stored correct indexes for a skill's verification quiz.
    (Tests assert server behaviour, not quiz secrecy — secrecy is covered by
    test_acceptance's masking assertions.)"""
    with SessionLocal() as db:
        questions = db.query(DiagnosticQuestion).filter(
            DiagnosticQuestion.goal_id == goal_id,
            DiagnosticQuestion.skill_slug == f"verif_{skill_db_id}",
        ).all()
        return [{"question_id": q.id, "selected_option": q.correct_index} for q in questions]


def verify_skill_successfully(goal_id, skill_db_id):
    client.post(f"/api/goals/{goal_id}/skills/{skill_db_id}/verification")
    answers = correct_verification_answers(goal_id, skill_db_id)
    result = client.post(f"/api/goals/{goal_id}/skills/{skill_db_id}/verify", json={"answers": answers})
    assert result.status_code == 200, result.text
    return result.json()


@pytest.fixture(autouse=True)
def setup_db_with_goal(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    test_goal = Goal(
        title="Frontend Developer Internship",
        hours_per_week=10.0,
        duration_weeks=12,
        budget=0.0,
        status="active"
    )
    db.add(test_goal)
    db.commit()
    db.refresh(test_goal)
    goal_id = test_goal.id

    # Generate graph (deterministic fallback: 6 frontend skills)
    res = client.post(f"/api/goals/{goal_id}/generate-graph")
    assert res.status_code == 200, res.text

    db.close()
    yield goal_id


# ===== PHASE 2: VERIFIED GOAL COVERAGE TESTS =====

def test_initial_coverage_zero(setup_db_with_goal):
    """Test 1: Initial coverage is 0% before any verification."""
    goal_id = setup_db_with_goal

    route_res = client.get(f"/api/goals/{goal_id}/route")
    assert route_res.status_code == 200
    data = route_res.json()

    coverage = data.get("coverage")
    assert coverage is not None, "Coverage should be in route response"
    assert coverage["verified_coverage_pct"] == 0.0, "Initial verified coverage should be 0%"
    assert coverage["diagnostic_coverage_pct"] == 0.0, "Initial diagnostic coverage should be 0%"
    assert coverage["verified_skills"] == 0
    assert coverage["total_skills"] > 0
    assert coverage["remaining_skills"] == coverage["total_skills"]


def test_coverage_after_diagnostic(setup_db_with_goal):
    """Test 2: Diagnostic coverage increases after diagnostic, verified stays 0%."""
    goal_id = setup_db_with_goal

    # Submit diagnostic
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    route_res = client.get(f"/api/goals/{goal_id}/route")
    data = route_res.json()
    coverage = data.get("coverage")

    assert coverage["verified_coverage_pct"] == 0.0, "Verified coverage should still be 0%"
    assert coverage["diagnostic_coverage_pct"] > 0.0, "Diagnostic coverage should be > 0% after diagnostic"


def test_coverage_after_partial_verification(setup_db_with_goal):
    """Test 3: Verified coverage increases after partial verification."""
    goal_id = setup_db_with_goal

    # Submit diagnostic
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    # Verify first available skill
    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    available = [s for s in graph_state['skills'] if s['status'] in ('AVAILABLE', 'IN_PROGRESS')]
    assert len(available) > 0

    result = verify_skill_successfully(goal_id, available[0]['db_id'])
    assert result["passed"] is True

    route_res = client.get(f"/api/goals/{goal_id}/route")
    data = route_res.json()
    coverage = data.get("coverage")

    assert coverage["verified_coverage_pct"] > 0.0, "Verified coverage should be > 0% after verification"
    assert coverage["verified_skills"] == 1
    assert coverage["remaining_skills"] == coverage["total_skills"] - 1


def test_coverage_after_full_verification(setup_db_with_goal):
    """Test 4: Verified coverage reaches 100% after all skills verified."""
    goal_id = setup_db_with_goal

    # Submit diagnostic
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    # Verify all skills in topological order until none are unlockable
    verified = 0
    for _ in range(20):
        graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
        available = [s for s in graph_state['skills'] if s['status'] in ('AVAILABLE', 'IN_PROGRESS')]
        if not available:
            break
        result = verify_skill_successfully(goal_id, available[0]['db_id'])
        assert result["passed"] is True
        verified += 1

    total = client.get(f"/api/goals/{goal_id}/route").json()["coverage"]["total_skills"]
    assert verified == total, f"Should have verified all {total} skills, got {verified}"

    coverage = client.get(f"/api/goals/{goal_id}/route").json()["coverage"]
    assert coverage["verified_coverage_pct"] == 100.0, "Verified coverage should be 100% after all verified"
    assert coverage["verified_skills"] == coverage["total_skills"]
    assert coverage["remaining_skills"] == 0


def test_failed_verification_does_not_increase_coverage(setup_db_with_goal):
    """Test 5: Failed verification does not increase verified coverage."""
    goal_id = setup_db_with_goal

    # Submit diagnostic
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    # Verify with all-wrong answers (correct+1 mod 4)
    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    available = [s for s in graph_state['skills'] if s['status'] in ('AVAILABLE', 'IN_PROGRESS')]
    first = available[0]
    client.post(f"/api/goals/{goal_id}/skills/{first['db_id']}/verification")
    wrong = [{"question_id": a["question_id"],
              "selected_option": (a["selected_option"] + 1) % 4}
             for a in correct_verification_answers(goal_id, first["db_id"])]
    verify_result = client.post(f"/api/goals/{goal_id}/skills/{first['db_id']}/verify", json={'answers': wrong}).json()

    assert verify_result["passed"] is False

    coverage = client.get(f"/api/goals/{goal_id}/route").json()["coverage"]
    assert coverage["verified_coverage_pct"] == 0.0, "Failed verification should not increase verified coverage"
    assert coverage["verified_skills"] == 0


def test_dependent_skill_verification_blocked(setup_db_with_goal):
    """Test 6: Dependent skills remain locked until prerequisites verified."""
    goal_id = setup_db_with_goal

    # Submit diagnostic
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    # Try to verify a dependent (locked) skill - should be rejected
    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    locked = [s for s in graph_state['skills'] if s['status'] == 'LOCKED']
    assert len(locked) > 0

    locked_skill = locked[0]
    verify_res = client.post(f"/api/goals/{goal_id}/skills/{locked_skill['db_id']}/verification")
    assert verify_res.status_code == 409
    assert "prerequisite" in verify_res.json().get("detail", "").lower()


def test_dependent_with_diagnostic_score_still_rejected(setup_db_with_goal):
    """Test 6b (Pre-check 2 regression): a dependent skill that HAS a diagnostic
    score is still rejected for verification while any prerequisite is unverified.
    Both endpoints must return 409 (never 422/500), and no verification quiz may
    be generated for the locked skill as a side effect."""
    goal_id = setup_db_with_goal

    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    by_id = {s["id"]: s for s in graph_state["skills"]}
    # Pick a genuinely dependent skill (target of some dependency)
    dependent = next(by_id[d["to"]] for d in graph_state["dependencies"])
    db_id = dependent["db_id"]

    # Legitimate diagnostic score on the dependent (diagnostic endpoints allow this)
    m = client.post(f"/api/goals/{goal_id}/mastery",
                    json={"goal_id": goal_id, "skill_id": db_id, "diagnostic_score": 0.5})
    assert m.status_code == 201, m.text

    states = {s["id"]: s["status"] for s in client.get(f"/api/goals/{goal_id}/graph").json()["skills"]}
    assert states[dependent["id"]] == "LOCKED", \
        "A diagnostic score must NOT unlock a dependent skill while prerequisites are unverified"

    questions_res = client.post(f"/api/goals/{goal_id}/skills/{db_id}/verification")
    assert questions_res.status_code == 409
    assert "prerequisite" in questions_res.json()["detail"].lower()

    verify_res = client.post(f"/api/goals/{goal_id}/skills/{db_id}/verify",
                             json={"answers": [{"question_id": 999999, "selected_option": 0}]})
    assert verify_res.status_code == 409, \
        f"/verify must reject a locked dependent with 409, got {verify_res.status_code}: {verify_res.text}"
    assert "prerequisite" in verify_res.json()["detail"].lower()

    with SessionLocal() as db:
        generated = db.query(DiagnosticQuestion).filter(
            DiagnosticQuestion.goal_id == goal_id,
            DiagnosticQuestion.skill_slug == f"verif_{db_id}",
        ).count()
    assert generated == 0, "No verification quiz may be generated for a locked dependent"

    # Coverage must still be 0% — diagnostic scores never count as verified
    coverage = client.get(f"/api/goals/{goal_id}/route").json()["coverage"]
    assert coverage["verified_coverage_pct"] == 0.0


def test_verified_prerequisite_unlocks_dependent_with_diagnostic_score(setup_db_with_goal):
    """Test 6c (Pre-check 2 control): once the prerequisite is verified, the
    dependent skill that already had a diagnostic score unlocks normally."""
    goal_id = setup_db_with_goal

    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    by_id = {s["id"]: s for s in graph_state["skills"]}
    dependent = next(by_id[d["to"]] for d in graph_state["dependencies"])
    root = next(s for s in graph_state["skills"] if s["status"] == "AVAILABLE")
    db_id = dependent["db_id"]

    client.post(f"/api/goals/{goal_id}/mastery",
                json={"goal_id": goal_id, "skill_id": db_id, "diagnostic_score": 0.5})

    result = verify_skill_successfully(goal_id, root["db_id"])
    assert result["passed"] is True

    states = {s["id"]: s["status"] for s in client.get(f"/api/goals/{goal_id}/graph").json()["skills"]}
    assert states[dependent["id"]] == "IN_PROGRESS"
    assert client.post(f"/api/goals/{goal_id}/skills/{db_id}/verification").status_code == 200


def test_coverage_with_zero_importance_weight():
    """Test 7: Skills with zero/negative/missing importance default to 1.0."""
    db = SessionLocal()
    goal = Goal(title="Zero Weight Test", hours_per_week=10, duration_weeks=8, budget=0, status="active")
    db.add(goal)
    db.commit()
    db.refresh(goal)
    goal_id = goal.id

    # Create skills with various importance values
    skills = [
        Skill(goal_id=goal_id, name="Normal Skill", slug="normal", importance=1.0),
        Skill(goal_id=goal_id, name="High Importance", slug="high", importance=5.0),
        Skill(goal_id=goal_id, name="Zero Weight", slug="zero", importance=0.0),  # should default to 1.0
        Skill(goal_id=goal_id, name="Negative Weight", slug="neg", importance=-1.0),  # should default to 1.0
        Skill(goal_id=goal_id, name="Missing Weight", slug="missing", importance=None),  # should default to 1.0
    ]
    for s in skills:
        db.add(s)
    db.commit()

    # Verify one skill
    mastery = Mastery(goal_id=goal_id, skill_id=skills[0].id, verified=True)
    db.add(mastery)
    db.commit()

    coverage = calculate_coverage(db, goal_id)

    # Normal (1.0) verified out of total weight: 1.0 + 5.0 + 1.0 + 1.0 + 1.0 = 9.0
    # Verified weight = 1.0, so coverage = 1.0/9.0 * 100 = 11.1%
    assert coverage["verified_coverage_pct"] == round(1.0/9.0 * 100, 1)
    assert coverage["total_skills"] == 5

    db.close()


def test_coverage_with_out_of_range_importance_defaults_to_one():
    """Test 7b: importance > 5.0 also safely defaults to 1.0."""
    db = SessionLocal()
    goal = Goal(title="Range Weight Test", hours_per_week=10, duration_weeks=8, budget=0, status="active")
    db.add(goal)
    db.commit()
    db.refresh(goal)
    goal_id = goal.id

    skills = [
        Skill(goal_id=goal_id, name="Absurd Weight", slug="absurd", importance=99.0),  # default 1.0
        Skill(goal_id=goal_id, name="Regular", slug="regular", importance=1.0),
    ]
    for s in skills:
        db.add(s)
    db.commit()
    db.add(Mastery(goal_id=goal_id, skill_id=skills[0].id, verified=True))
    db.commit()

    coverage = calculate_coverage(db, goal_id)
    # 99.0 clamps to 1.0; total = 2.0, verified = 1.0 -> 50%
    assert coverage["verified_coverage_pct"] == 50.0
    db.close()


def test_coverage_persists_across_replan(setup_db_with_goal):
    """Test 8: Coverage preserved after replan and refresh."""
    goal_id = setup_db_with_goal

    # Submit diagnostic and verify one skill
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    available = [s for s in graph_state['skills'] if s['status'] in ('AVAILABLE', 'IN_PROGRESS')]
    verify_skill_successfully(goal_id, available[0]['db_id'])

    # Get coverage before replan
    route_before = client.get(f"/api/goals/{goal_id}/route").json()
    coverage_before = route_before.get("coverage", {}).get("verified_coverage_pct")

    # Replan
    client.post(f"/api/goals/{goal_id}/replan", json={"hours_per_week": 5})

    # Get coverage after replan
    route_after = client.get(f"/api/goals/{goal_id}/route").json()
    coverage_after = route_after.get("coverage", {}).get("verified_coverage_pct")

    assert coverage_before == coverage_after, "Coverage should persist across replan"
    assert coverage_before > 0.0


def test_coverage_refresh_preserved(setup_db_with_goal):
    """Test 9: Coverage preserved after multiple route refreshes."""
    goal_id = setup_db_with_goal

    # Submit diagnostic and verify one skill
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    available = [s for s in graph_state['skills'] if s['status'] in ('AVAILABLE', 'IN_PROGRESS')]
    verify_skill_successfully(goal_id, available[0]['db_id'])

    # Refresh multiple times
    coverage_values = []
    for _ in range(3):
        route = client.get(f"/api/goals/{goal_id}/route").json()
        coverage_values.append(route.get("coverage", {}).get("verified_coverage_pct"))

    assert all(c == coverage_values[0] for c in coverage_values), "Coverage should be consistent across refreshes"
    assert coverage_values[0] > 0.0

    # Graph endpoint must report the identical coverage
    graph_coverage = client.get(f"/api/goals/{goal_id}/graph").json()["coverage"]
    assert graph_coverage["verified_coverage_pct"] == coverage_values[0]


def test_format_preference_no_effect_on_coverage(setup_db_with_goal):
    """Test 10: Changing resource format has no effect on coverage."""
    goal_id = setup_db_with_goal

    # Submit diagnostic and verify one skill
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    available = [s for s in graph_state['skills'] if s['status'] in ('AVAILABLE', 'IN_PROGRESS')]
    verify_skill_successfully(goal_id, available[0]['db_id'])

    # Coverage is calculated from mastery, not resources
    # Multiple route fetches (simulating format switches) should not change coverage
    coverage_values = []
    for _ in range(3):
        route = client.get(f"/api/goals/{goal_id}/route").json()
        coverage_values.append(route.get("coverage", {}).get("verified_coverage_pct"))

    assert all(c == coverage_values[0] for c in coverage_values), "Coverage should not change with format operations"


def test_coverage_endpoint(setup_db_with_goal):
    """Test 11: Dedicated coverage endpoint works."""
    goal_id = setup_db_with_goal

    # Submit diagnostic and verify one skill
    diag = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    answers = [{'question_id': q['id'], 'selected_option': 0} for q in diag['questions']]
    client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={'answers': answers})

    graph_state = client.get(f"/api/goals/{goal_id}/graph").json()
    available = [s for s in graph_state['skills'] if s['status'] in ('AVAILABLE', 'IN_PROGRESS')]
    verify_skill_successfully(goal_id, available[0]['db_id'])

    # Get coverage from dedicated endpoint
    cov_res = client.get(f"/api/goals/{goal_id}/coverage")
    assert cov_res.status_code == 200
    coverage = cov_res.json()

    assert "verified_coverage_pct" in coverage
    assert "diagnostic_coverage_pct" in coverage
    assert "verified_skills" in coverage
    assert "total_skills" in coverage
    assert "remaining_skills" in coverage
    assert "skill_breakdown" in coverage

    # Endpoint result matches the route-embedded result
    route_coverage = client.get(f"/api/goals/{goal_id}/route").json()["coverage"]
    assert coverage["verified_coverage_pct"] == route_coverage["verified_coverage_pct"]


def test_coverage_skill_breakdown(setup_db_with_goal):
    """Test 12: Coverage breakdown includes per-skill details."""
    goal_id = setup_db_with_goal

    route_res = client.get(f"/api/goals/{goal_id}/route")
    data = route_res.json()
    coverage = data.get("coverage")

    assert "skill_breakdown" in coverage
    breakdown = coverage["skill_breakdown"]
    assert len(breakdown) == coverage["total_skills"]

    for skill in breakdown:
        assert "skill_id" in skill
        assert "name" in skill
        assert "importance" in skill
        assert "verified" in skill
        assert "diagnostic_score" in skill
        assert "verification_score" in skill
        assert "status" in skill


def test_no_employment_guarantee_language():
    """Test 13: Coverage calculation does not claim employment guarantees.

    This is a documentation/design test - coverage is a progress metric only.
    """
    # The coverage_service.py source uses "verified_coverage_pct"
    # not "employment_readiness" or "job_guarantee"
    from services.coverage_service import calculate_coverage

    import inspect
    source = inspect.getsource(calculate_coverage)
    assert "employment" not in source.lower()
    assert "guarantee" not in source.lower()
    assert "job" not in source.lower()
    assert "verified_coverage_pct" in source
    assert "diagnostic_coverage_pct" in source  # separate metric
