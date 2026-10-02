import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import Base, engine, SessionLocal
from models.goal import Goal

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db_with_goal():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Create test goal
    test_goal = Goal(
        title="Frontend Developer Internship",
        hours_per_week=7.0,
        duration_weeks=12,
        budget=0.0,
        status="active"
    )
    db.add(test_goal)
    db.commit()
    db.refresh(test_goal)
    goal_id = test_goal.id

    # Generate graph first so skills exist
    client.post(f"/api/goals/{goal_id}/generate-graph")

    db.close()
    yield goal_id


def test_generate_diagnostic_masking(setup_db_with_goal):
    """Test 1: Diagnostic questions generated and correct_index/explanation are MASKED from public response."""
    goal_id = setup_db_with_goal

    response = client.post(f"/api/goals/{goal_id}/diagnostic")
    assert response.status_code == 200

    data = response.json()
    assert data["goal_id"] == goal_id
    assert "questions" in data
    assert len(data["questions"]) > 0

    first_q = data["questions"][0]
    assert "id" in first_q
    assert "skill_id" in first_q
    assert "skill_name" in first_q
    assert "question" in first_q
    assert "options" in first_q
    assert len(first_q["options"]) == 4

    # SECURITY ASSERTIONS: Must NOT expose correct_index or explanation before submission!
    assert "correct_index" not in first_q
    assert "explanation" not in first_q


def test_submit_diagnostic_grading_and_persistence(setup_db_with_goal):
    """Test 2 & 3: Diagnostic submission grades answers, updates DB Mastery table, and persists across GET calls."""
    goal_id = setup_db_with_goal

    # 1. Fetch questions
    diag_res = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    questions = diag_res["questions"]

    # 2. Submit answers
    user_answers = [
        {"question_id": q["id"], "selected_option": 0}
        for q in questions
    ]

    submit_res = client.post(
        f"/api/goals/{goal_id}/diagnostic/submit",
        json={"answers": user_answers}
    )
    assert submit_res.status_code == 200

    submit_data = submit_res.json()
    assert submit_data["goal_id"] == goal_id
    assert "mastery" in submit_data
    assert len(submit_data["mastery"]) > 0

    first_mastery = submit_data["mastery"][0]
    assert "skill_id" in first_mastery
    assert "score" in first_mastery
    assert isinstance(first_mastery["score"], int)

    # 3. Test Persistence: GET /api/goals/{goal_id}/diagnostic/mastery must retrieve persisted mastery scores
    get_res = client.get(f"/api/goals/{goal_id}/diagnostic/mastery")
    assert get_res.status_code == 200

    get_data = get_res.json()
    assert get_data["goal_id"] == goal_id
    assert len(get_data["mastery"]) == len(submit_data["mastery"])
    assert get_data["mastery"][0]["score"] == first_mastery["score"]
    assert all(m["assessed"] is True for m in get_data["mastery"])


# ===== GOAL-AWARE DIAGNOSTIC DISTRIBUTION (learner-journey overhaul) =====

def _graph_skills(goal_id):
    return client.get(f"/api/goals/{goal_id}/graph").json()["skills"]


def test_quick_diagnostic_covers_every_skill(setup_db_with_goal):
    """Quick assessment: one question per skill — the count reflects the graph,
    and no skill is silently left unassessed on small graphs."""
    goal_id = setup_db_with_goal
    skills = _graph_skills(goal_id)
    assert len(skills) == 6  # deterministic fallback frontend graph

    data = client.post(f"/api/goals/{goal_id}/diagnostic").json()
    questions = data["questions"]

    assert len(questions) == len(skills), \
        f"Quick diagnostic should ask 1 question per skill ({len(skills)}), got {len(questions)}"
    covered = {q["skill_db_id"] for q in questions}
    assert covered == {s["db_id"] for s in skills}, "Every skill must be assessed"


def test_quick_diagnostic_is_idempotent(setup_db_with_goal):
    """Calling the diagnostic endpoint twice must not grow the question set."""
    goal_id = setup_db_with_goal
    first = client.post(f"/api/goals/{goal_id}/diagnostic").json()["questions"]
    second = client.post(f"/api/goals/{goal_id}/diagnostic").json()["questions"]
    assert [q["id"] for q in first] == [q["id"] for q in second]


def test_deep_diagnostic_tops_up_to_two_per_skill(setup_db_with_goal):
    """Deep assessment: preserves existing questions, tops up to 2 per skill (capped)."""
    goal_id = setup_db_with_goal
    skills = _graph_skills(goal_id)
    quick = client.post(f"/api/goals/{goal_id}/diagnostic").json()["questions"]
    assert len(quick) == len(skills)

    deep = client.post(f"/api/goals/{goal_id}/diagnostic?depth=deep").json()["questions"]
    assert len(deep) == 2 * len(skills), "Deep should ask 2 questions per skill on a 6-skill graph"
    assert {q["id"] for q in quick} <= {q["id"] for q in deep}, "Deep must preserve existing questions"

    per_skill = {}
    for q in deep:
        per_skill[q["skill_db_id"]] = per_skill.get(q["skill_db_id"], 0) + 1
    assert all(v == 2 for v in per_skill.values())
    assert set(per_skill) == {s["db_id"] for s in skills}


def test_deep_diagnostic_caps_at_twelve(setup_db_with_goal):
    """Deep assessment on a large graph respects the 12-question cap."""
    from models.skill import Skill
    from db.database import SessionLocal

    goal_id = setup_db_with_goal
    db = SessionLocal()
    for i in range(4, 12):  # grow the 6-skill graph to 14 skills
        db.add(Skill(goal_id=goal_id, name=f"Extra Topic {i}", slug=f"extra_topic_{i}"))
    db.commit()
    db.close()

    deep = client.post(f"/api/goals/{goal_id}/diagnostic?depth=deep").json()["questions"]
    assert len(deep) <= 12, "Deep diagnostic must cap at 12 questions"
    assert all(not q["skill_name"].startswith("Extra Topic") for q in deep), "Unsupported topics must not receive fabricated questions"


def test_unassessed_skills_get_no_fabricated_scores(setup_db_with_goal):
    """Skills beyond the question cap stay UNASSESSED: no mastery row, no score."""
    from models.skill import Skill
    from db.database import SessionLocal

    goal_id = setup_db_with_goal
    db = SessionLocal()
    for i in range(4, 12):  # 14 skills total: quick cap 10 -> 4 unassessed
        db.add(Skill(goal_id=goal_id, name=f"Extra Topic {i}", slug=f"extra_topic_{i}"))
    db.commit()
    db.close()

    questions = client.post(f"/api/goals/{goal_id}/diagnostic").json()["questions"]
    assert len(questions) == 6  # Only six topics have a reliable curated assessment.

    answers = [{"question_id": q["id"], "selected_option": q.get("selected_option", 0)} for q in questions]
    submit = client.post(f"/api/goals/{goal_id}/diagnostic/submit", json={"answers": answers})
    assert submit.status_code == 200

    mastery = client.get(f"/api/goals/{goal_id}/diagnostic/mastery").json()["mastery"]
    assessed_ids = {m["skill_db_id"] for m in mastery}
    assert assessed_ids == {q["skill_db_id"] for q in questions}, \
        "Only assessed skills may have mastery rows"

    # Every assessed row carries a real score; unassessed skills are simply absent
    # (the UI labels them UNASSESSED rather than showing a fabricated 0%).
