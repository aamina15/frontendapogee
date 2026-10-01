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
