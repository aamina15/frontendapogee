import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import Base, engine, SessionLocal
from models.goal import Goal
from services.resource_service import find_verified_resource_for_skill

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db_with_goal():
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

    # Generate graph
    client.post(f"/api/goals/{goal_id}/generate-graph")

    db.close()
    yield goal_id


def test_verified_resource_lookup_real_urls():
    """Test 1: Standard skills map to real verified URLs and valid duration_hours."""
    html_res = find_verified_resource_for_skill("HTML5 & Modern CSS Layouts", "html_css")
    assert html_res is not None
    assert "developer.mozilla.org" in html_res["url"]
    assert html_res["duration_hours"] > 0

    pytorch_res = find_verified_resource_for_skill("PyTorch Deep Learning", "deep_learning")
    assert pytorch_res is not None
    assert "pytorch.org" in pytorch_res["url"]
    assert pytorch_res["duration_hours"] > 0


def test_missing_resource_honest_state():
    """Test 2: Skills with no catalogued resource return None (honest missing state)."""
    unknown_res = find_verified_resource_for_skill("Quantum Topological Computing 9000", "quantum_xyz")
    assert unknown_res is None


def test_route_planner_calculates_hours_from_duration(setup_db_with_goal):
    """Test 3: Route planner sums duration_hours and calculates total_weeks using hours_per_week."""
    goal_id = setup_db_with_goal

    route_res = client.get(f"/api/goals/{goal_id}/route")
    assert route_res.status_code == 200

    data = route_res.json()
    assert data["goal_id"] == goal_id
    assert "phases" in data
    assert len(data["phases"]) > 0

    # Verify total_hours equals sum of resource duration_hours
    calculated_hours = 0.0
    for phase in data["phases"]:
        assert "duration_weeks" in phase
        assert "hours_total" in phase
        for res in phase["resources"]:
            assert "duration_hours" in res
            assert res["duration_hours"] > 0
            if res["has_resource"]:
                assert res["url"] is not None
                assert res["url"].startswith("http")
            calculated_hours += res["duration_hours"]

    assert data["total_hours"] == calculated_hours
    assert data["total_weeks"] > 0
